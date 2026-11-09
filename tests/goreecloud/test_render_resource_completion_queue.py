"""Prevent regression to unbounded renderer completion queues.

Source checks cover wiring across document resets; compiled Rust capacity and
owned-loopback rendering remain mandatory GitHub CI gates.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RenderResourceCompletionQueueTests(unittest.TestCase):
    def test_completed_resource_capacity_matches_inflight_limit(self):
        code = (ROOT / "crates/obscura-js/src/ops.rs").read_text()
        self.assertIn("MAX_PENDING_RENDER_RESOURCE_RESULTS: usize = RENDER_RESOURCE_CONCURRENCY", code)
        self.assertIn("pub render_resource_tx: tokio::sync::mpsc::Sender<RenderResourceLoad>", code)
        self.assertIn("pub render_resource_rx: tokio::sync::mpsc::Receiver<RenderResourceLoad>", code)
        self.assertNotIn("UnboundedSender<RenderResourceLoad>", code)
        self.assertNotIn("UnboundedReceiver<RenderResourceLoad>", code)
        self.assertIn("fn render_result_queue_refuses_excess_and_recovers()", code)

    def test_all_document_reinitializations_keep_bounded_channel(self):
        code = (ROOT / "crates/obscura-js/src/runtime.rs").read_text()
        self.assertEqual(
            code.count("tokio::sync::mpsc::channel(crate::ops::MAX_PENDING_RENDER_RESOURCE_RESULTS)"),
            3,
        )
        self.assertIn("tx.send(load).await.is_err()", code)
        self.assertIn("state.render_resource_rx.try_recv()", code)
        self.assertNotIn("UnboundedSender<_>", code)


if __name__ == "__main__":
    unittest.main()
