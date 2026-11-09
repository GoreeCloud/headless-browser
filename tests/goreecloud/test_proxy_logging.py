"""Static regression guard for accidental proxy credential logging."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ProxyLoggingSafety(unittest.TestCase):
    def test_cli_never_formats_raw_proxy_into_existing_status_log(self):
        cli = (ROOT / "crates/obscura-cli/src/main.rs").read_text(encoding="utf-8")
        self.assertNotIn('tracing::info!("Using proxy: {}", proxy)', cli)
        self.assertEqual(cli.count('tracing::info!("Proxy configured (details redacted)")'), 2)

    def test_security_guidance_warns_against_argv_secrets(self):
        guidance = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("OBSCURA_PROXY", guidance)
        self.assertIn("process arguments", guidance)


if __name__ == "__main__":
    unittest.main()
