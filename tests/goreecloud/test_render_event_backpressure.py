"""Source wiring checks for bounded, lossless render event admission.

Compiled Rust tests and owned-loopback CI, not these checks alone, are the
behavioral evidence for event ordering, capacity and generation cleanup.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class RenderEventBackpressureWiringTests(unittest.TestCase):
    def test_renderer_admission_budget_is_enforced_before_receive(self):
        code = (ROOT / "crates/obscura-js/src/runtime.rs").read_text()
        self.assertIn("MAX_PENDING_RENDER_RESOURCE_EVENTS: usize = 8", code)
        self.assertIn("MAX_PENDING_RENDER_EVENT_BODY_BYTES: usize = 64 * 1024 * 1024", code)
        self.assertIn("let budget = render_event_admission_slots(&state);", code)
        self.assertIn("for _ in 0..budget {", code)
        self.assertIn("match state.render_resource_rx.try_recv()", code)
        self.assertNotIn("while let Ok(load) = state.render_resource_rx.try_recv()", code)
        self.assertIn("pub fn take_render_resource_events", code)

    def test_existing_channel_capacity_and_lifecycle_retained(self):
        ops = (ROOT / "crates/obscura-js/src/ops.rs").read_text()
        runtime = (ROOT / "crates/obscura-js/src/runtime.rs").read_text()
        self.assertIn("MAX_PENDING_RENDER_RESOURCE_RESULTS: usize = RENDER_RESOURCE_CONCURRENCY", ops)
        self.assertIn("render_resource_events.clear();", runtime)
        self.assertIn("pending_render_resource_event_budget_preserves_fifo_and_recovers_after_drain", runtime)


if __name__ == "__main__":
    unittest.main()
