"""Offline assertions for fail-closed CDP startup test runner."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import verify_cdp_startup_security as gate


class StartupHarnessTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        binary = self.root / "target/debug/goreecloud-headless-browser"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"unexecuted-fixture")
        patch = mock.patch.object(gate, "ROOT", self.root)
        patch.start()
        self.addCleanup(patch.stop)

    def verify_case(self, result=None):
        if result is None:
            result = subprocess.CompletedProcess([], 1, b"", b"refusing to expose CDP without authentication")
        with mock.patch.object(gate.subprocess, "run", return_value=result) as runner:
            gate.reject_startup(
                binary="goreecloud-headless-browser",
                host="192.0.2.123",
                token=None,
                expected_error="refusing to expose CDP without authentication",
            )
            self.assertEqual(runner.call_count, 1)
            args = runner.call_args.args[0]
            self.assertEqual(args[args.index("--host") + 1], "192.0.2.123")
            self.assertEqual(args[args.index("--port") + 1], "0")
            self.assertIn("--ready-file", args)
            options = runner.call_args.kwargs
            self.assertFalse(options["check"])
            self.assertTrue(options["capture_output"])
            self.assertEqual(options["timeout"], 8)
            self.assertNotIn("OBSCURA_CDP_TOKEN", options["env"])

    def test_negative_startup_validation(self):
        self.verify_case()

    def test_successful_exit_is_not_a_denial(self):
        with self.assertRaisesRegex(AssertionError, "expected startup guard"):
            self.verify_case(subprocess.CompletedProcess([], 0, b"", b""))

    def test_wrong_failure_reason_is_not_a_denial(self):
        with self.assertRaisesRegex(AssertionError, "expected startup guard"):
            self.verify_case(subprocess.CompletedProcess([], 1, b"", b"other failure"))

    def test_timeout_must_fail_closed(self):
        with mock.patch.object(
            gate.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired("cdp-test", 8),
        ):
            with self.assertRaisesRegex(AssertionError, "did not exit promptly"):
                gate.reject_startup(
                    binary="goreecloud-headless-browser",
                    host="127.0.0.1",
                    token="short-token",
                    expected_error="OBSCURA_CDP_TOKEN must be at least 32 bytes",
                )

    def test_missing_binary_is_rejected_without_running_any_process(self):
        with mock.patch.object(gate.subprocess, "run") as runner:
            with self.assertRaisesRegex(AssertionError, "unbuilt"):
                gate.reject_startup(
                    binary="obscura",
                    host="127.0.0.1",
                    token=None,
                    expected_error="some guard",
                )
            runner.assert_not_called()

    def test_forwarded_settings_are_explicitly_passed_and_sanitized(self):
        with mock.patch.object(gate.subprocess, "run") as runner:
            runner.return_value = subprocess.CompletedProcess(
                [], 1, b"", b"refusing to expose CDP without authentication"
            )
            gate.reject_startup(
                binary="goreecloud-headless-browser",
                host="127.0.0.1",
                token=None,
                forwarded={
                    "OBSCURA_CDP_FORWARDED_HOST": "0.0.0.0",
                    "OBSCURA_CDP_FORWARDED_PORT": "9222",
                },
                expected_error="refusing to expose CDP without authentication",
            )
            env = runner.call_args.kwargs["env"]
            self.assertEqual(env["OBSCURA_CDP_FORWARDED_HOST"], "0.0.0.0")
            self.assertEqual(env["OBSCURA_CDP_FORWARDED_PORT"], "9222")
            self.assertEqual(env["OBSCURA_ALLOW_PRIVATE_NETWORK"], "0")


if __name__ == "__main__":
    unittest.main()
