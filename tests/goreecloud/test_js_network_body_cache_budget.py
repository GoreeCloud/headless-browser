"""Verify JS completion caching accounts for actual String byte retention.

Compiled hosted Rust checks remain authoritative for behavior and ordering.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class JSNetworkBodyCacheBudgetWiringTests(unittest.TestCase):
    def test_js_completion_uses_aggregate_byte_and_entry_limits(self):
        src = (ROOT / "crates/obscura-js/src/ops.rs").read_text()
        self.assertIn("fn response_body_total_byte_limit() -> usize", src)
        self.assertIn("OBSCURA_NETWORK_BODY_BUFFER_TOTAL_BYTES", src)
        self.assertIn("unwrap_or(32 * 1024 * 1024)", src)
        self.assertIn("body.body.len() > max_total_bytes", src)
        self.assertIn("trim_js_network_body_cache(gs, max_entries, max_total_bytes)", src)
        self.assertIn("store_js_network_body(gs, event.request_id.clone(), body(), max_entries, total_bytes)", src)
        self.assertIn("push_js_network_event(gs, event);", src)

    def test_source_has_rust_regressions_for_duplicates_and_event_preservation(self):
        src = (ROOT / "crates/obscura-js/src/ops.rs").read_text()
        self.assertIn("js_network_body_cache_aggregate_budget_accounts_for_strings_and_duplicate_ids", src)
        self.assertIn("js_network_body_cache_retains_completion_events_when_caching_is_refused", src)
        self.assertIn("gs.network_response_body_order.retain(|id| id != &request_id)", src)


if __name__ == "__main__":
    unittest.main()
