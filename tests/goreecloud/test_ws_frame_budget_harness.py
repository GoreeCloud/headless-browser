"""Purely local tests for the bounded inbound WebSocket header fixture."""

import struct
import unittest
from pathlib import Path

from scripts import verify_cdp_ws_frame_budget as budget


class WebSocketBudgetFixtureTests(unittest.TestCase):
    def test_masked_64_bit_length_header_has_expected_size(self):
        data = budget.oversized_masked_header(b"abcd")
        self.assertEqual(len(data), 14)
        self.assertEqual(data[:2], b"\x81\xff")
        self.assertEqual(data[10:], b"abcd")
        self.assertEqual(struct.unpack("!Q", data[2:10])[0], 16 * 1024 * 1024 + 1)

    def test_mask_length_is_enforced(self):
        for mask in (b"", b"a", b"abc", b"abcde"):
            with self.subTest(mask=mask), self.assertRaisesRegex(ValueError, "four-byte"):
                budget.oversized_masked_header(mask)

    def test_rust_policy_limit_matches_test_header(self):
        path = Path(__file__).resolve().parents[2] / "crates/obscura-cdp/src/server.rs"
        source = path.read_text(encoding="utf-8")
        self.assertIn(
            "const MAX_CDP_INBOUND_MESSAGE_BYTES: usize = 16 * 1024 * 1024;",
            source,
        )
        self.assertIn(
            "config.max_message_size = Some(MAX_CDP_INBOUND_MESSAGE_BYTES)",
            source,
        )
        self.assertIn(
            "config.max_frame_size = Some(MAX_CDP_INBOUND_MESSAGE_BYTES)",
            source,
        )


if __name__ == "__main__":
    unittest.main()
