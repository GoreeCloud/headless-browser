"""Source checks for bounded Runtime event queues and count-only CDP gaps.

Compiled Rust plus owned-loopback GitHub CI remain required for behavior.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class RuntimeEventBudgetWiringTests(unittest.TestCase):
    def test_three_js_runtime_event_producers_share_byte_budget(self):
        src = (ROOT / "crates/obscura-js/src/ops.rs").read_text()
        self.assertIn("MAX_PENDING_RUNTIME_EVENTS: usize = 1_024", src)
        self.assertIn("MAX_RUNTIME_EVENT_METADATA_BYTES: usize = 256 * 1_024", src)
        self.assertIn("MAX_PENDING_RUNTIME_EVENT_METADATA_BYTES: usize = 8 * 1_024 * 1_024", src)
        self.assertIn("fn json_retained_metadata_bytes(", src)
        self.assertIn("fn runtime_event_retained_bytes(", src)
        self.assertIn("fn push_runtime_event(", src)
        self.assertIn("pending_runtime_events_dropped", src)
        self.assertIn("if args_json.len() > MAX_RUNTIME_EVENT_METADATA_BYTES", src)
        self.assertIn("push_runtime_event(&mut state, RuntimeEvent::DocumentLifecycle", src)
        self.assertIn("push_runtime_event(state, RuntimeEvent::Exception", src)
        self.assertIn("push_runtime_event(&mut page, RuntimeEvent::Console", src)
        self.assertIn("goreecloud_runtime_event_budget_tests", src)

    def test_count_only_gap_is_drained_and_target_scoped(self):
        runtime = (ROOT / "crates/obscura-js/src/runtime.rs").read_text()
        browser = (ROOT / "crates/obscura-browser/src/page.rs").read_text()
        dispatch = (ROOT / "crates/obscura-cdp/src/dispatch.rs").read_text()
        self.assertIn("take_pending_runtime_events_with_overflow(&mut self)", runtime)
        self.assertIn("state.pending_runtime_event_bytes = 0", runtime)
        self.assertIn("std::mem::take(&mut state.pending_runtime_events_dropped)", runtime)
        self.assertIn("take_pending_runtime_events_with_overflow(", browser)
        self.assertIn("append_runtime_overflow_notices(", dispatch)
        self.assertIn('method: "GoreeCloud.runtimeEventOverflow".to_string()', dispatch)
        self.assertIn('json!({"source": "runtime", "droppedEvents": dropped})', dispatch)
        self.assertIn("goreecloud_runtime_event_overflow_notifies_only_same_target_subscribers", dispatch)


if __name__ == "__main__":
    unittest.main()
