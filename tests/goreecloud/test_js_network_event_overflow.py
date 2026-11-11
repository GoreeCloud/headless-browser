"""Source-level guards for explicit count-only JS Network queue overflow telemetry."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class JSNetworkEventOverflowWiringTests(unittest.TestCase):
    def test_js_queue_overflow_count_and_atomic_drain_are_present(self):
        js = (ROOT / "crates/obscura-js/src/ops.rs").read_text()
        runtime = (ROOT / "crates/obscura-js/src/runtime.rs").read_text()
        page = (ROOT / "crates/obscura-browser/src/page.rs").read_text()
        self.assertIn("const MAX_JS_NETWORK_EVENTS: usize = 4096;", js)
        self.assertIn("js_network_events_dropped.saturating_add(overflow as u64)", js)
        self.assertIn("std::mem::take(&mut state.js_network_events_dropped)", runtime)
        self.assertIn("take_js_network_events_with_overflow()", page)
        self.assertIn("dropped_js_events_before: if index == 0 { dropped } else { 0 }", page)

    def test_cdp_extension_is_count_only_and_fans_out_to_observers(self):
        cdp = (ROOT / "crates/obscura-cdp/src/domains/page.rs").read_text()
        self.assertIn('method: "GoreeCloud.networkEventOverflow".into()', cdp)
        self.assertIn('json!({"source": "javascript", "droppedEvents": dropped})', cdp)
        self.assertIn('if network_event.dropped_js_events_before > 0', cdp)
        self.assertIn('if net_event.dropped_js_events_before > 0', cdp)
        self.assertIn('"GoreeCloud.networkEventOverflow")', cdp)
        self.assertIn('fn goreecloud_js_event_overflow_is_not_a_fake_network_request_and_fans_out()', cdp)
        self.assertIn('fn goreecloud_js_event_overflow_survives_navigation_event_phasing()', cdp)


if __name__ == "__main__":
    unittest.main()
