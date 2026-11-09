"""Offline checks for the local CDP control-plane smoke harness."""

from unittest import TestCase, mock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from pathlib import Path

from scripts.verify_cdp_loopback_smoke import sanitized_env, validate_ready, raw_get_version, serve_command


VALID_READY = {
    "pid": 321,
    "host": "127.0.0.1",
    "port": 39001,
    "websocket_path": "/devtools/browser",
}


class CdpHarnessTests(TestCase):
    def test_raw_http_client_preserves_duplicate_header_fields(self):
        class Receiver(BaseHTTPRequestHandler):
            def do_GET(self):
                count = len(self.headers.get_all("Host", []))
                body = b'{"error":"duplicate"}'
                self.send_response(403 if count == 2 else 200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            status, data = raw_get_version(server.server_port, [
                "Host: 127.0.0.1",
                "hOsT: 127.0.0.1",
            ])
            self.assertEqual(status, 403)
            self.assertIn(b"duplicate", data)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_private_network_optin_must_be_explicit_in_serve_args(self):
        binary = Path("/tmp/inert-cli")
        ready = Path("/tmp/inert-ready.json")
        default = serve_command(binary, ready)
        opted = serve_command(binary, ready, allow_private_network=True)
        self.assertNotIn("--allow-private-network", default)
        self.assertEqual(opted[-1], "--allow-private-network")
        self.assertEqual(opted[:-1], default)
        self.assertEqual(default[default.index("--host") + 1], "127.0.0.1")

    def test_max_connections_requires_positive_integer(self):
        for invalid in (0, -1, True, 1.5, "1"):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "positive integer"):
                serve_command(Path("/tmp/inert"), Path("/tmp/ready"), max_connections=invalid)

    def test_max_connections_is_explicit_and_does_not_relax_network_guard(self):
        command = serve_command(Path("/tmp/inert"), Path("/tmp/ready"), max_connections=1)
        self.assertEqual(command[-2:], ["--max-connections", "1"])
        self.assertNotIn("--allow-private-network", command)
        self.assertEqual(command[command.index("--host") + 1], "127.0.0.1")

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
