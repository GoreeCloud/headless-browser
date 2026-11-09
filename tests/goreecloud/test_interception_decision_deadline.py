"""Verify JavaScript and document interception share the bounded decision wait.

These source-level checks prevent accidental removal of the wiring. Rust
behavior remains subject to the compiled CI regression suite.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class InterceptionDecisionDeadlineWiringTests(unittest.TestCase):
    def test_single_shared_sixty_second_deadline(self):
        ops = (ROOT / "crates/obscura-js/src/ops.rs").read_text()
        self.assertIn("INTERCEPTION_DECISION_WAIT", ops)
        self.assertIn("std::time::Duration::from_secs(60)", ops)
        self.assertIn("tokio::time::timeout(limit, receiver)", ops)
        self.assertIn("match await_interception_resolution(resolve_rx).await", ops)
        self.assertNotIn("match resolve_rx.await", ops)

    def test_document_navigation_uses_same_fail_closed_deadline(self):
        page = (ROOT / "crates/obscura-browser/src/page.rs").read_text()
        self.assertIn("obscura_js::ops::await_interception_resolution(resolution).await", page)
        self.assertIn('reason == "interception decision timed out"', page)
        self.assertIn('"net::ERR_TIMED_OUT"', page)
        self.assertNotIn("let response = match resolution.await", page)


if __name__ == "__main__":
    unittest.main()
