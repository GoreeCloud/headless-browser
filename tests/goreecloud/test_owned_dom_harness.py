"""Offline unit tests for owned HTTP fixture and CDP DOM smoke contract."""

import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from scripts import verify_cdp_owned_dom_smoke as smoke


class FixturePeer:
    def __init__(self, responses=None):
        self.calls = []
        self.responses = {
            21: {"targetId": "owned-target"},
            22: {"sessionId": "owned-session"},
            23: {
                "result": {"type": "string", "value": smoke.EXPECTED_TEXT},
            },
            24: {"success": True},
        }
        self.responses.update(responses or {})

    def request(self, message_id, method, *, params=None, session_id=None):
        self.calls.append((message_id, method, params, session_id))
        return self.responses[message_id]


class OwnedDomSmokeTests(unittest.TestCase):
    def test_static_owned_fixture_is_local_only_and_inert(self):
        self.assertNotIn(b"http://", smoke.HTML_BODY)
        self.assertNotIn(b"https://", smoke.HTML_BODY)
        self.assertNotIn(b"<script", smoke.HTML_BODY)
        with smoke.owned_http_page() as (url, hits):
            self.assertTrue(url.startswith("http://127.0.0.1:"))
            with urlopen(url, timeout=3) as response:
                self.assertEqual(response.read(), smoke.HTML_BODY)
                self.assertIn("text/html", response.headers["Content-Type"])
            self.assertEqual(hits, ["/owned"])

    def test_fixture_rejects_other_paths(self):
        with smoke.owned_http_page() as (url, _hits):
            with self.assertRaises(HTTPError) as got:
                urlopen(url.replace("/owned", "/unrelated"), timeout=3)
            self.assertEqual(got.exception.code, 404)

    def test_owned_target_and_trusted_dom_are_verified_and_closed(self):
        peer = FixturePeer()
        smoke.validate_owned_dom(peer, "http://127.0.0.1:10001/owned")
        self.assertEqual([row[1] for row in peer.calls], [
            "Target.createTarget",
            "Target.attachToTarget",
            "Runtime.evaluate",
            "Target.closeTarget",
        ])
        self.assertEqual(peer.calls[0][2]["url"], "http://127.0.0.1:10001/owned")
        self.assertEqual(peer.calls[2][3], "owned-session")
        self.assertEqual(peer.calls[2][2]["returnByValue"], True)

    def test_wrong_dom_value_fails_but_still_closes_target(self):
        peer = FixturePeer({23: {"result": {"type": "string", "value": "wrong"}}})
        with self.assertRaisesRegex(AssertionError, "did not match"):
            smoke.validate_owned_dom(peer, "http://127.0.0.1:10001/owned")
        self.assertEqual(peer.calls[-1][1], "Target.closeTarget")

    def test_no_session_fails_but_still_closes_target(self):
        peer = FixturePeer({22: {}})
        with self.assertRaisesRegex(AssertionError, "no session"):
            smoke.validate_owned_dom(peer, "http://127.0.0.1:10001/owned")
        self.assertEqual(peer.calls[-1][1], "Target.closeTarget")

    def test_missing_target_identity_is_rejected(self):
        peer = FixturePeer({21: {"targetId": ""}})
        with self.assertRaisesRegex(AssertionError, "target ID"):
            smoke.validate_owned_dom(peer, "http://127.0.0.1:10001/owned")


if __name__ == "__main__":
    unittest.main()
