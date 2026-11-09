"""Offline fixture checks for the exact CDP HTTP route smoke harness."""

import unittest
from urllib.parse import urlsplit

from scripts.verify_cli_loopback_smoke import LocalFixture, PAYLOAD
from scripts.verify_cdp_exact_http_route import request_status


class ExactRouteHarnessTests(unittest.TestCase):
    def test_owned_loopback_fixture_accepts_only_known_path(self):
        with LocalFixture() as fixture:
            port = urlsplit(fixture.url).port
            self.assertIsNotNone(port)
            code, payload = request_status(port, "/fixture")
            self.assertEqual(code, 200)
            self.assertEqual(payload, PAYLOAD)
            code, _ = request_status(port, "/fixture-lookalike")
            self.assertEqual(code, 404)
            self.assertEqual(fixture.hits, ["/fixture", "/fixture-lookalike"])

    def test_rejects_absolute_urls_and_header_injection(self):
        for target in ("http://external.invalid/json/version",
                       "//external.invalid/json/version",
                       "/json/version\r\nHost: external.invalid",
                       "/json/version\nInjected: bad",
                       "", "a" * 201):
            with self.subTest(target=target), self.assertRaises(ValueError):
                request_status(9222, target)


if __name__ == "__main__":
    unittest.main()
