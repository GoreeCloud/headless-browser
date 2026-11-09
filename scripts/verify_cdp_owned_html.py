#!/usr/bin/env python3
"""Trusted local HTML + CDP navigation/DOM smoke on an owned loopback fixture.

No third-party pages, external navigation, arbitrary remote scripts,
publication or public CDP binding. Only tested under explicit trusted
--allow-private-network on a disposable hosted CI runner.
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterator
from urllib.parse import urlsplit

if __package__:
    from .verify_cdp_loopback_smoke import disposable_cdp_server
    from .verify_cdp_websocket_smoke import BufferedConnection, handshake
else:
    from verify_cdp_loopback_smoke import disposable_cdp_server
    from verify_cdp_websocket_smoke import BufferedConnection, handshake

TITLE = "GoreeCloud Owned Local HTML"
BODY_TEXT = "Safe offline browser fixture"
HTML_BYTES = (
    b"<!doctype html><html><head><meta charset='UTF-8'>"
    b"<title>GoreeCloud Owned Local HTML</title></head>"
    b"<body><h1 id='proof'>Safe offline browser fixture</h1></body></html>"
)
PATH = "/owned-fixture.html"


class LocalHtmlHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.server.hits.append(self.path)  # type: ignore[attr-defined]
        if self.path != PATH:
            self.send_error(404, "fixture path not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(HTML_BYTES)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(HTML_BYTES)

    def log_message(self, format: str, *args: object) -> None:
        pass


@contextmanager
def owned_html_fixture() -> Iterator[tuple[str, list[str]]]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalHtmlHandler)
    server.hits = []  # type: ignore[attr-defined]
    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
        name="goreecloud-local-html-fixture",
    )
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}{PATH}", server.hits  # type: ignore[attr-defined]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def trusted_navigation(peer: BufferedConnection, url: str) -> None:
    # Verify the complete authority structurally: a prefix such as
    # http://127.0.0.1:1234@external.invalid/... is NOT loopback.
    parsed = urlsplit(url)
    try:
        valid_port = parsed.port is not None and 1 <= parsed.port <= 65535
    except ValueError:
        valid_port = False
    if not (
        parsed.scheme == "http"
        and parsed.hostname == "127.0.0.1"
        and parsed.username is None
        and parsed.password is None
        and valid_port
        and parsed.netloc == f"127.0.0.1:{parsed.port}"
        and parsed.path == PATH
        and not parsed.query
        and not parsed.fragment
    ):
        raise AssertionError("HTML CDP navigation must use the owned-loopback fixture")

    opened = peer.request(41, "Target.createTarget", params={"url": "about:blank"})
    target_id = opened.get("targetId")
    if not isinstance(target_id, str) or not target_id:
        raise AssertionError("fixture target creation failed")
    attached = peer.request(
        42, "Target.attachToTarget",
        params={"targetId": target_id, "flatten": True},
    )
    session = attached.get("sessionId")
    if not isinstance(session, str) or not session:
        raise AssertionError("fixture session attach failed")

    try:
        navigated = peer.request(
            43, "Page.navigate",
            params={"url": url},
            session_id=session,
        )
        if "errorText" in navigated and navigated["errorText"]:
            raise AssertionError("owned local navigation failed")

        # Some network and event plumbing can complete after the reply.
        # Poll only two stable DOM reads, with an overall bounded retry.
        ready = False
        for attempt in range(12):
            title = peer.request(
                100 + attempt * 2, "Runtime.evaluate",
                params={"expression": "document.title", "returnByValue": True},
                session_id=session,
            )
            heading = peer.request(
                101 + attempt * 2, "Runtime.evaluate",
                params={
                    "expression": "document.getElementById('proof')?.textContent?.trim()",
                    "returnByValue": True,
                },
                session_id=session,
            )
            if title.get("result", {}).get("value") == TITLE and heading.get("result", {}).get("value") == BODY_TEXT:
                ready = True
                break
            time.sleep(0.1)
        if not ready:
            raise AssertionError("owned HTML fixture title/DOM were not loaded")
    finally:
        closed = peer.request(44, "Target.closeTarget", params={"targetId": target_id})
        if closed.get("success") is not True:
            raise AssertionError("fixture target cleanup failed")


def main() -> None:
    with owned_html_fixture() as (url, hits):
        # Explicitly confined to this owned loopback server, never untrusted
        # webpages. The private-network opt-in is not a production default.
        with disposable_cdp_server(
            "goreecloud-headless-browser", allow_private_network=True
        ) as port:
            with handshake(port) as (status, peer):
                if status != 101:
                    raise AssertionError("local HTML CDP websocket refused")
                trusted_navigation(peer, url)

        if PATH not in hits:
            raise AssertionError("owned HTML fixture was never reached")
        if any(path not in (PATH, "/favicon.ico") for path in hits):
            raise AssertionError("unexpected URL requested from owned fixture")

    print("PASS: explicit-opt-in loopback CDP fetched HTML and evaluated its title and DOM")


if __name__ == "__main__":
    main()
