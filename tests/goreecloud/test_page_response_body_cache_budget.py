"""Source checks guarding aggregate Page Network response body cache admission."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ResponseBodyCacheBudgetWiringTests(unittest.TestCase):
    def test_normal_alias_and_suspension_use_aggregate_budget(self):
        src = (ROOT / "crates/obscura-browser/src/page.rs").read_text()
        self.assertIn('fn response_body_total_byte_limit() -> usize', src)
        self.assertIn('OBSCURA_NETWORK_BODY_BUFFER_TOTAL_BYTES', src)
        self.assertIn('unwrap_or(32 * 1024 * 1024)', src)
        self.assertIn('self.trim_response_body_cache(max_entries, max_total_bytes)', src)
        self.assertIn('self.trim_response_body_cache(', src)
        self.assertIn('response_body_entry_limit(), response_body_total_byte_limit(),', src)
        self.assertIn('self.store_response_body(id, &raw, body.base64_encoded);', src)
        self.assertIn('self.response_body_order.retain(|id| id != &request_id);', src)

    def test_compiled_regressions_track_aliases_streaming_and_eviction(self):
        src = (ROOT / "crates/obscura-browser/src/page.rs").read_text()
        self.assertIn('fn page_response_body_aggregate_budget_evicts_oldest_and_counts_aliases()', src)
        self.assertIn('fn page_response_body_aggregate_budget_recovers_after_stream_transfer()', src)
        self.assertIn('self.response_bodies.values().fold(0_usize', src)


if __name__ == "__main__":
    unittest.main()
