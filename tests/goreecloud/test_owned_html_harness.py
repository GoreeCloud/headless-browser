"""No-network regression checks for the owned-loopback HTML/CDP smoke."""

from __future__ import annotations

import http.client
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.request import urlopen

from scripts import verify_cdp_owned_html as gate


class FakePeer:
    def __init__(self, overrides: dict[int, dict] | None = None) -> None:
        self.calls: list[tuple[int, str, dict | None, str | None]] = []
        self.overrides = overrides or {}

    def request(
        self,
        message_id: int,
        method: str,
        *,
        params: dict | None = None,
        session_id: str | None = None,
    ) -> dict:
        self.calls.append((message_id, method, params, session_id))
        if message_id in self.overrides:
            return self.overrides[message_id]
        replies = {
            41: {"targetId": "fixture-target"},
            42: {"sessionId": "fixture-session"},
            43: {"frameId": "test-frame"},
            44: {"success": True},
        }
        if message_id % 2 == 0 and message_id >= 100:
            return {"result": {"type": "string", "value": gate.TITLE}}
        if message_id % 2 == 1 and message_id >= 101:
            return {"result": {"type": "string", "value": gate.BODY_TEXT}}
        return replies[message_id]


OWNED_URL = "http://127.0.0.1:49001/owned-fixture.html"


class OwnedHtmlTests(unittest.TestCase):
    def test_fixture_content_and_CSP(self):
        with gate.owned_html_fixture() as (url, hits):
            with urlopen(url, timeout=3) as response:
                self.assertEqual(response.read(), gate.HTML_BYTES)
                self.assertIn("default-src 'none'", response.headers["Content-Security-Policy"])
            self.assertEqual(hits, [gate.PATH])

    def test_fixture_rejects_other_path(self):
        with gate.owned_html_fixture() as (url, hits):
            with self.assertRaises(HTTPError) as failure:
                urlopen(url.replace(gate.PATH, "/forbidden"), timeout=3)
            self.assertEqual(failure.exception.code, 404)
            self.assertEqual(hits, ["/forbidden"])

    def test_controlled_navigation_and_cleanup(self):
        peer = FakePeer()
        gate.trusted_navigation(peer, OWNED_URL)
        names = [x[1] for x in peer.calls]
        self.assertEqual(names[:3], [
            "Target.createTarget", "Target.attachToTarget", "Page.navigate",
        ])
        self.assertEqual(names[-1], "Target.closeTarget")
        self.assertEqual(peer.calls[2][2], {"url": OWNED_URL})
        self.assertEqual(peer.calls[2][3], "fixture-session")
        self.assertEqual(peer.calls[3][2]["expression"], "document.title")
        self.assertEqual(peer.calls[4][2]["expression"], "document.getElementById('proof')?.textContent?.trim()")

    def test_remote_navigation_refused_without_contacting_peer(self):
        for url in ("https://example.invalid/owned-fixture.html",
                    "http://10.0.0.1:49001/owned-fixture.html",
                    "file:///etc/passwd",
                    "http://127.0.0.1:49001/not-fixture",
                    "http://127.0.0.1:49001@evil.invalid/owned-fixture.html",
                    "http://127.0.0.1:99999/owned-fixture.html",
                    "http://127.0.0.1:49001/owned-fixture.html?redirect=http://evil.invalid",
                    "http://127.0.0.1:49001/owned-fixture.html#fragment"):
            peer = FakePeer()
            with self.subTest(url=url), self.assertRaisesRegex(AssertionError, "owned-loopback"):
                gate.trusted_navigation(peer, url)
            self.assertFalse(peer.calls)

    def test_target_missing_refused(self):
        with self.assertRaisesRegex(AssertionError, "creation failed"):
            gate.trusted_navigation(FakePeer({41: {"targetId": None}}), OWNED_URL)

    def test_session_missing_refused(self):
        with self.assertRaisesRegex(AssertionError, "attach failed"):
            gate.trusted_navigation(FakePeer({42: {"sessionId": ""}}), OWNED_URL)

    def test_navigation_error_still_closes_target(self):
        peer = FakePeer({43: {"errorText": "refused"}})
        with self.assertRaisesRegex(AssertionError, "navigation failed"):
            gate.trusted_navigation(peer, OWNED_URL)
        self.assertEqual(peer.calls[-1][1], "Target.closeTarget")

    def test_unexpected_dom_cannot_pass(self):
        peer = FakePeer({100: {"result": {"value": "wrong title"}}})
        # The first attempt fails but subsequent polls should recover.
        with mock.patch.object(gate.time, "sleep"):
            gate.trusted_navigation(peer, OWNED_URL)
        self.assertIn(102, [i for i, *_ in peer.calls])

    def test_wrong_dom_fails_bounded_poll_and_still_cleans_up(self):
        class WrongDOM(FakePeer):
            def request(self, message_id, method, *, params=None, session_id=None):
                if method == "Runtime.evaluate":
                    self.calls.append((message_id, method, params, session_id))
                    return {"result": {"type": "string", "value": "wrong DOM"}}
                return super().request(message_id, method, params=params, session_id=session_id)

        peer = WrongDOM()
        with mock.patch.object(gate.time, "sleep") as sleep:
            with self.assertRaisesRegex(AssertionError, "title/DOM were not loaded"):
                gate.trusted_navigation(peer, OWNED_URL)
        self.assertEqual(sleep.call_count, 12)
        self.assertEqual(peer.calls[-1][1], "Target.closeTarget")

    def test_cleanup_failure_cannot_silently_pass(self):
        with self.assertRaisesRegex(AssertionError, "cleanup failed"):
            gate.trusted_navigation(FakePeer({44: {"success": False}}), OWNED_URL)


if __name__ == "__main__":
    unittest.main()
