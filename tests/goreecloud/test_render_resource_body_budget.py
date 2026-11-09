"""Verify the render-only per-response memory policy stays on the real fetch path.

Source wiring checks supplement, but do not replace, protected CI's feature-
gated Rust test and owned-loopback PNG/PDF validation.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RenderResourceBodyBudgetTests(unittest.TestCase):
    def test_renderer_loader_uses_bounded_http_transport_request(self):
        runtime = (ROOT / "crates/obscura-js/src/runtime.rs").read_text()
        self.assertIn("MAX_RENDER_BACKGROUND_RESPONSE_BYTES: usize = 16 * 1024 * 1024", runtime)
        self.assertIn("request.max_response_bytes.min(MAX_RENDER_BACKGROUND_RESPONSE_BYTES)", runtime)
        self.assertIn("let mut request = bounded_render_resource_request(kind, &initiator)", runtime)
        self.assertNotIn("let mut request = ResourceRequest::subresource(kind, &initiator);", runtime)
        self.assertIn("renderer_image_and_font_transfers_cap_decoded_response_bytes", runtime)

    def test_queue_count_cap_remains_independent(self):
        ops = (ROOT / "crates/obscura-js/src/ops.rs").read_text()
        self.assertIn("MAX_PENDING_RENDER_RESOURCE_RESULTS: usize = RENDER_RESOURCE_CONCURRENCY", ops)
        self.assertIn("pub const RENDER_RESOURCE_CONCURRENCY: usize = 16", ops)


if __name__ == "__main__":
    unittest.main()
