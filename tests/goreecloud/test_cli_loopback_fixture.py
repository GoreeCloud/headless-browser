"""Offline regression checks for the owned-loopback executable smoke harness."""

from pathlib import Path
from unittest import TestCase, mock
from urllib.error import HTTPError
from urllib.request import urlopen

from scripts import verify_cli_loopback_smoke as smoke


class LoopbackHarnessTests(TestCase):
    def test_fixture_is_binary_not_text(self):
        self.assertEqual(smoke.PAYLOAD[0], 0)
        self.assertEqual(smoke.PAYLOAD[-1], 0)
        self.assertIn(255, smoke.PAYLOAD)

    def test_owned_fixture_serves_verbatim_bytes(self):
        with smoke.LocalFixture() as fixture:
            self.assertTrue(fixture.url.startswith("http://127.0.0.1:"))
            with urlopen(fixture.url, timeout=3) as response:
                self.assertEqual(response.read(), smoke.PAYLOAD)
            self.assertEqual(fixture.hits, ["/fixture"])

    def test_unknown_fixture_route_is_not_served(self):
        with smoke.LocalFixture() as fixture:
            with self.assertRaises(HTTPError) as got:
                urlopen(fixture.url.replace("/fixture", "/missing"), timeout=3)
            self.assertEqual(got.exception.code, 404)

    def test_browser_invocation_clears_inherited_proxy(self):
        with mock.patch.dict(
            "os.environ",
            {"HTTP_PROXY": "http://secret:token@proxy.invalid:8000", "OBSCURA_PROXY": "secret"},
        ), mock.patch.object(smoke.subprocess, "run") as call:
            smoke.launch(Path("/tmp/fake-browser"), "--help")
            options = call.call_args.kwargs
            self.assertEqual(options["env"]["OBSCURA_ALLOW_PRIVATE_NETWORK"], "0")
            self.assertNotIn("HTTP_PROXY", options["env"])
            self.assertNotIn("OBSCURA_PROXY", options["env"])
            self.assertEqual(options["timeout"], 25)
            self.assertTrue(options["capture_output"])


if __name__ == "__main__":
    import unittest
    unittest.main()
