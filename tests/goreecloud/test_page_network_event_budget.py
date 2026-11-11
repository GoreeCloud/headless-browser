"""Source wiring for bounded Page Network event metadata and count-only CDP notices.

These are regression guards; hosted Rust and owned-loopback CDP/browser tests
provide behavioral evidence.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class PageNetworkEventBudgetWiringTests(unittest.TestCase):
    def test_page_centralizes_network_event_insertion_and_counted_loss(self):
        source = (ROOT / "crates/obscura-browser/src/page.rs").read_text()
        self.assertIn("MAX_PAGE_NETWORK_EVENTS: usize = 512", source)
        self.assertIn("MAX_PAGE_NETWORK_EVENT_METADATA_BYTES: usize = 4 * 1024 * 1024", source)
        self.assertIn("fn append_network_event(&mut self, event: NetworkEvent)", source)
        self.assertIn("fn network_event_metadata_bytes(event: &NetworkEvent)", source)
        self.assertIn("self.pending_page_network_event_drops.saturating_add(1)", source)
        self.assertIn("pending_js_overflow_notices_without_survivor", source)
        self.assertIn("self.append_network_event(NetworkEvent", source)
        self.assertIn("pub fn take_network_event_overflow_counts(&mut self)", source)

    def test_all_cdp_drain_paths_emit_privacy_minimized_counts(self):
        files = ["crates/obscura-cdp/src/server.rs",
                 "crates/obscura-cdp/src/domains/page.rs",
                 "crates/obscura-cdp/src/domains/runtime.rs"]
        names = [((ROOT / file).read_text(), file) for file in files]
        for source, file in names:
            with self.subTest(file=file):
                self.assertIn("emit_page_network_event_pressure(", source)
                self.assertIn("take_network_event_overflow_counts()", source)
        cdp = names[1][0]
        self.assertIn('"GoreeCloud.networkEventOverflow"', cdp)
        self.assertIn('json!({"source": source, "droppedEvents": dropped})', cdp)
        self.assertIn("network_observer_sessions(ctx, page_id, source_session)", cdp)
        self.assertIn("goreecloud_page_event_overflow_reports_count_only_to_same_target_observers", cdp)


if __name__ == "__main__":
    unittest.main()
