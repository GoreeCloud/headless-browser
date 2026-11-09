"""Offline checks for the local CDP control-plane smoke harness."""

from unittest import TestCase, mock

from scripts.verify_cdp_loopback_smoke import sanitized_env, validate_ready


VALID_READY = {
    "pid": 321,
    "host": "127.0.0.1",
    "port": 39001,
    "websocket_path": "/devtools/browser",
}


class CdpHarnessTests(TestCase):
    def test_valid_owned_loopback_ready_record(self):
        self.assertEqual(validate_ready(VALID_READY, 321), 39001)

    def test_wrong_pid_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "process"):
            validate_ready(VALID_READY, 99)

    def test_nonloopback_bind_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "nonloopback"):
            validate_ready({**VALID_READY, "host": "0.0.0.0"}, 321)

    def test_unexpected_protocol_endpoint_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "endpoint"):
            validate_ready({**VALID_READY, "websocket_path": "/unreviewed"}, 321)

    def test_invalid_ports_are_rejected(self):
        for value in (0, 65536, True, "39001", -1):
            with self.subTest(value=value), self.assertRaisesRegex(AssertionError, "port"):
                validate_ready({**VALID_READY, "port": value}, 321)

    def test_malformed_record_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "object"):
            validate_ready([], 321)

    def test_environment_strips_proxies_and_forwarded_authority(self):
        with mock.patch.dict(
            "os.environ",
            {
                "HTTP_PROXY": "http://secret:password@proxy.invalid",
                "OBSCURA_PROXY": "http://secret@proxy.invalid",
                "OBSCURA_CDP_TOKEN": "inherited-secret",
                "OBSCURA_CDP_FORWARDED_HOST": "0.0.0.0",
                "OBSCURA_CDP_FORWARDED_PORT": "9222",
                "OBSCURA_ALLOW_PRIVATE_NETWORK": "1",
            },
        ):
            env = sanitized_env(None)
        for key in (
            "HTTP_PROXY", "OBSCURA_PROXY", "OBSCURA_CDP_TOKEN",
            "OBSCURA_CDP_FORWARDED_HOST", "OBSCURA_CDP_FORWARDED_PORT",
        ):
            self.assertNotIn(key, env)
        self.assertEqual(env["OBSCURA_ALLOW_PRIVATE_NETWORK"], "0")

    def test_explicit_ephemeral_bearer_token_is_passed_without_logging(self):
        env = sanitized_env("temporary-not-a-real-production-secret")
        self.assertEqual(env["OBSCURA_CDP_TOKEN"], "temporary-not-a-real-production-secret")
        self.assertEqual(env["RUST_LOG"], "off")


if __name__ == "__main__":
    import unittest
    unittest.main()
