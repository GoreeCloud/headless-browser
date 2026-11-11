"""Source wiring checks for optional buffered JS/Page console memory caps.

Hosted Rust tests and owned-loopback smoke are the behavioral verification.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ConsoleRetentionBudgetWiringTests(unittest.TestCase):
    def test_js_console_buffer_is_limited_before_retention(self):
        source = (ROOT / "crates/obscura-js/src/ops.rs").read_text()
        self.assertIn("MAX_BUFFERED_CONSOLE_MESSAGES: usize = 1_024", source)
        self.assertIn("MAX_BUFFERED_CONSOLE_MESSAGE_BYTES: usize = 16 * 1_024", source)
        self.assertIn("MAX_BUFFERED_CONSOLE_TOTAL_BYTES: usize = 2 * 1_024 * 1_024", source)
        self.assertIn("msg.is_char_boundary(end)", source)
        self.assertIn("CONSOLE_TRUNCATION_MARKER", source)
        self.assertIn("push_bounded_console_message(&mut page.pending_console_messages, level, msg)", source)
        self.assertIn("goreecloud_bounded_console_buffer_tests", source)
        self.assertNotIn('push_back(format!("[{level}] {msg}"))', source)

    def test_page_suspension_uses_same_retention_budget(self):
        page = (ROOT / "crates/obscura-browser/src/page.rs").read_text()
        self.assertIn("self.trim_suspended_console_messages();", page)
        self.assertIn("fn trim_suspended_console_messages(&mut self)", page)
        self.assertIn("obscura_js::ops::MAX_BUFFERED_CONSOLE_TOTAL_BYTES", page)
        self.assertIn("obscura_js::ops::MAX_BUFFERED_CONSOLE_MESSAGES", page)
        self.assertIn("suspended_console_backlog_caps_repeated_runtime_transfers", page)


if __name__ == "__main__":
    unittest.main()
