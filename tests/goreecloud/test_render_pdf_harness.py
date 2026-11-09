"""No-external-network tests for raster PDF CDP smoke validation."""

from __future__ import annotations

import base64
import unittest

from scripts import verify_render_pdf_smoke as check


OWNED_URL = "http://127.0.0.1:49000/owned"
VALID_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type /Catalog>>endobj\n"
    b"/MediaBox [0 0 288.000 432.000]\n"
    b"/Subtype /Image\n"
    + b"% deterministic document fixture\n" * 8
    + b"%%EOF\n"
)


class FixturePeer:
    def __init__(self, overrides=None):
        self.max_response_bytes = 64 * 1024
        self.calls = []
        self.overrides = overrides or {}

    def request(self, id, method, *, params=None, session_id=None):
        self.calls.append((id, method, params, session_id))
        defaults = {
            201: {"targetId": "trusted-pdf"},
            202: {"sessionId": "trusted-session"},
            203: {"result": {"type": "string", "value": "GoreeCloud Owned Fixture|fixture-ok"}},
            204: {"obscuraPrintMode": "print-media-raster", "data": base64.b64encode(VALID_PDF).decode()},
            205: {"success": True},
        }
        return self.overrides.get(id, defaults[id])


class RenderPdfTests(unittest.TestCase):
    def test_minimal_expected_raster_pdf_envelope(self):
        check.verify_pdf(VALID_PDF)

    def test_rejects_truncated_pdf(self):
        with self.assertRaisesRegex(ValueError, "EOF"):
            check.verify_pdf(VALID_PDF[:-6])

    def test_rejects_wrong_media_box(self):
        with self.assertRaisesRegex(ValueError, "geometry"):
            check.verify_pdf(VALID_PDF.replace(b"288.000", b"300.000"))

    def test_rejects_pdf_without_raster_image(self):
        with self.assertRaisesRegex(ValueError, "image"):
            check.verify_pdf(VALID_PDF.replace(b"/Subtype /Image", b"/Subtype /Other"))

    def test_rejects_non_pdf_bytes(self):
        with self.assertRaisesRegex(ValueError, "version"):
            check.verify_pdf(b"NOTPDF" + VALID_PDF[6:])

    def test_cdp_print_lifecycle_and_cleanup(self):
        peer = FixturePeer()
        check.run_print_job(peer, OWNED_URL)
        self.assertEqual([v[1] for v in peer.calls], [
            "Target.createTarget", "Target.attachToTarget", "Runtime.evaluate",
            "Page.printToPDF", "Target.closeTarget",
        ])
        self.assertEqual(peer.max_response_bytes, check.MAX_WIRE_PDF_REPLY_BYTES)
        self.assertEqual(peer.calls[3][3], "trusted-session")
        self.assertEqual(peer.calls[3][2]["paperWidth"], 4.0)
        self.assertTrue(peer.calls[3][2]["printBackground"])

    def test_malformed_pdf_must_fail_but_cleanup_occurs(self):
        peer = FixturePeer({204: {
            "obscuraPrintMode": "print-media-raster",
            "data": base64.b64encode(b"bad pdf").decode(),
        }})
        with self.assertRaises(ValueError):
            check.run_print_job(peer, OWNED_URL)
        self.assertEqual(peer.calls[-1][1], "Target.closeTarget")

    def test_missing_page_session_prevents_pdf(self):
        peer = FixturePeer({202: {"sessionId": None}})
        with self.assertRaisesRegex(AssertionError, "not attached"):
            check.run_print_job(peer, OWNED_URL)
        self.assertEqual(peer.calls[-1][1], "Target.closeTarget")

    def test_unsupported_remote_url_refused_before_cdp(self):
        peer = FixturePeer()
        for url in ("http://127.0.0.1:49000@evil.invalid/owned",
                    "http://10.0.0.1:49000/owned",
                    "file:///etc/passwd"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                check.run_print_job(peer, url)
        self.assertFalse(peer.calls)


if __name__ == "__main__":
    unittest.main()
