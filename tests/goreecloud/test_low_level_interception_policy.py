"""Ensure matching low-level intercepts cannot silently bypass a missing consumer.

Source wiring checks are supplementary; Rust and owned-loopback behavior are
tested by the required, nonpublishing GitHub Actions workflow.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class LowLevelInterceptionPolicyTests(unittest.TestCase):
    def test_js_sender_selection_fails_closed(self):
        ops = (ROOT / "crates/obscura-js/src/ops.rs").read_text()
        self.assertIn('fn select_interception_sender(', ops)
        self.assertIn('sender.cloned().map(Some).ok_or("interception consumer unavailable")', ops)
        self.assertIn('let itx = match select_interception_sender(', ops)
        self.assertIn('"blocked": true, "error": reason', ops)
        self.assertNotIn('let itx = if should_intercept_url(', ops)

    def test_document_navigation_missing_consumer_is_blocked(self):
        page = (ROOT / "crates/obscura-browser/src/page.rs").read_text()
        self.assertIn('let Some(tx) = &self.intercept_tx else {', page)
        self.assertIn('"net::ERR_BLOCKED_BY_CLIENT: interception consumer unavailable"', page)
        self.assertNotIn('let Some(tx) = &self.intercept_tx else { return Ok(None); };', page)
        self.assertIn('low_level_intercept_navigation_requires_a_consumer_for_matching_requests', page)


if __name__ == "__main__":
    unittest.main()
