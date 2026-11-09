#!/usr/bin/env python3
"""Owned-loopback CDP raster PDF smoke with render-enabled CLI only.

The only HTML is an inert 127.0.0.1 fixture; no third-party pages, host files,
remote CDP listeners, publishing, or retained PDF artifacts are involved.
"""

from __future__ import annotations

import base64

if __package__:
    from .verify_cdp_owned_dom_smoke import owned_http_page
    from .verify_cdp_loopback_smoke import disposable_cdp_server
    from .verify_cdp_websocket_smoke import BufferedConnection, handshake
    from .verify_render_png_smoke import validate_fixture_url
else:
    from verify_cdp_owned_dom_smoke import owned_http_page
    from verify_cdp_loopback_smoke import disposable_cdp_server
    from verify_cdp_websocket_smoke import BufferedConnection, handshake
    from verify_render_png_smoke import validate_fixture_url

MAX_WIRE_PDF_REPLY_BYTES = 8 * 1024 * 1024
MAX_PDF_BYTES = 6 * 1024 * 1024
EXPECTED_MEDIABOX = b"/MediaBox [0 0 288.000 432.000]"


def verify_pdf(raw: bytes) -> None:
    if not 200 <= len(raw) <= MAX_PDF_BYTES:
        raise ValueError("PDF size is outside the owned-fixture budget")
    if not raw.startswith(b"%PDF-1.4"):
        raise ValueError("missing raster PDF version header")
    if not raw.endswith(b"%%EOF\n"):
        raise ValueError("missing PDF EOF marker")
    if EXPECTED_MEDIABOX not in raw:
        raise ValueError("PDF paper geometry differs from the explicit 4x6 inch page")
    if b"/Subtype /Image" not in raw:
        raise ValueError("expected raster image data is absent")


def run_print_job(peer: BufferedConnection, url: str) -> None:
    validate_fixture_url(url)
    created = peer.request(201, "Target.createTarget", params={"url": url})
    target_id = created.get("targetId")
    if not isinstance(target_id, str) or not target_id:
        raise AssertionError("owned PDF target was not created")
    try:
        session = peer.request(
            202, "Target.attachToTarget", params={"targetId": target_id, "flatten": True}
        ).get("sessionId")
        if not isinstance(session, str) or not session:
            raise AssertionError("owned PDF target was not attached")

        dom = peer.request(
            203,
            "Runtime.evaluate",
            params={
                "expression": 'document.title + "|" + document.querySelector("#marker").textContent',
                "returnByValue": True,
            },
            session_id=session,
        )
        if dom.get("result", {}).get("value") != "GoreeCloud Owned Fixture|fixture-ok":
            raise AssertionError("render PDF source did not load expected owned document")

        # The Base64 image-containing response can exceed the default 64-KiB
        # metadata fixture cap; broaden only this owned fixture connection.
        peer.max_response_bytes = MAX_WIRE_PDF_REPLY_BYTES
        response = peer.request(
            204,
            "Page.printToPDF",
            params={
                "paperWidth": 4.0,
                "paperHeight": 6.0,
                "marginTop": 0.5,
                "marginBottom": 0.5,
                "marginLeft": 0.5,
                "marginRight": 0.5,
                "printBackground": True,
                "transferMode": "ReturnAsBase64",
            },
            session_id=session,
        )
        if response.get("obscuraPrintMode") != "print-media-raster":
            raise AssertionError("unexpected CDP PDF rendering mode")
        encoded = response.get("data")
        if not isinstance(encoded, str) or len(encoded) > min(
            MAX_WIRE_PDF_REPLY_BYTES, 4 * ((MAX_PDF_BYTES + 2) // 3)
        ):
            raise AssertionError("PDF response is absent or exceeds the expected bound")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (ValueError, base64.binascii.Error) as error:
            raise AssertionError("CDP PDF did not return valid base64") from error
        verify_pdf(data)
    finally:
        closed = peer.request(205, "Target.closeTarget", params={"targetId": target_id})
        if closed.get("success") is not True:
            raise AssertionError("owned PDF target cleanup failed")


def main() -> None:
    with owned_http_page() as (url, hits):
        with disposable_cdp_server("goreecloud-headless-browser", allow_private_network=True) as port:
            with handshake(port) as (status, peer):
                if status != 101:
                    raise AssertionError("owned-loopback PDF CDP websocket upgrade failed")
                run_print_job(peer, url)

        if "/owned" not in hits:
            raise AssertionError("PDF renderer did not fetch the owned HTML fixture")
        if any(hit not in ("/owned", "/favicon.ico") for hit in hits):
            raise AssertionError("unexpected HTTP request to the owned fixture")

    print("PASS: render-enabled CDP generated valid raster PDF of owned HTML with 4x6 inch page")


if __name__ == "__main__":
    main()
