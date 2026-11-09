"""Offline regression tests for the optional render screenshot fixture."""

from __future__ import annotations

import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

from scripts import verify_render_png_smoke as check


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack("!I", len(payload)) + kind + payload
        + struct.pack("!I", zlib.crc32(kind + payload))
    )


def make_png(width: int = 64, height: int = 32) -> bytes:
    ihdr = struct.pack("!IIBBBBB", width, height, 8, 6, 0, 0, 0)
    pixels = (b"\x00" + bytes(width * 4)) * height
    return (
        check.PNG_SIGNATURE
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(pixels))
        + png_chunk(b"IEND", b"")
    )


class RenderPngFixtureTests(unittest.TestCase):
    def test_valid_png_dimensions_and_integrity(self):
        self.assertEqual(check.validate_png(make_png()), (64, 32))

    def test_invalid_magic_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not a PNG"):
            check.validate_png(b"\x00" + make_png()[1:])

    def test_invalid_ihdr_checksum_is_rejected(self):
        damaged = bytearray(make_png())
        damaged[29] ^= 0x01
        with self.assertRaisesRegex(ValueError, "checksum"):
            check.validate_png(bytes(damaged))

    def test_missing_png_ending_rejected(self):
        with self.assertRaisesRegex(ValueError, "IEND"):
            check.validate_png(make_png()[:-12] + b"not-an-IEND")

    def test_bad_dimensions_rejected(self):
        for dims in ((0, 1), (5000, 1), (1, 0)):
            with self.subTest(dims=dims), self.assertRaisesRegex(ValueError, "dimensions"):
                check.validate_png(make_png(*dims))

    def test_owned_loopback_url_is_accepted(self):
        check.validate_fixture_url("http://127.0.0.1:49152/owned")

    def test_host_camouflage_and_unowned_url_are_rejected(self):
        for url in (
            "http://127.0.0.1:49152@evil.invalid/owned",
            "http://127.0.0.1:49152/other",
            "http://127.0.0.1:49152/owned?evil=1",
            "http://127.0.0.1:49152/owned#fragment",
            "http://127.0.0.1:99999/owned",
            "https://127.0.0.1:49152/owned",
            "http://10.1.1.5:49152/owned",
            "file:///tmp/owned",
        ):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, "owned fixture"):
                check.validate_fixture_url(url)

    def test_execution_is_bounded_and_env_has_no_inherited_proxy(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            binary = root / "target/debug/goreecloud-headless-browser"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"not-a-real-executable")
            with mock.patch.object(check, "ROOT", root), mock.patch.dict(
                "os.environ",
                {"HTTP_PROXY": "http://token:secret@proxy.invalid",
                 "OBSCURA_SHOT_W": "9999"},
            ), mock.patch.object(check.subprocess, "run") as runner:
                check.render_owned_url("http://127.0.0.1:49152/owned", root / "out.png")
                args = runner.call_args.args[0]
                opts = runner.call_args.kwargs
                self.assertIn("--allow-private-network", args)
                self.assertIn("--screenshot", args)
                self.assertEqual(opts["timeout"], 70)
                self.assertTrue(opts["capture_output"])
                self.assertNotIn("HTTP_PROXY", opts["env"])
                self.assertNotIn("OBSCURA_SHOT_W", opts["env"])


if __name__ == "__main__":
    unittest.main()
