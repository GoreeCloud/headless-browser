#!/usr/bin/env python3
"""Owned-loopback HTTP navigation and DOM smoke with explicit SSRF opt-in.

Uses only a fixed inert HTML page on 127.0.0.1 and no external references,
scripts, images, cookies, credentials or other network destinations.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterator

if __package__:
    from .verify_cdp_loopback_smoke import disposable_cdp_server
    from .verify_cdp_websocket_smoke import BufferedConnection, handshake
else:
    from verify_cdp_loopback_smoke import disposable_cdp_server
    from verify_cdp_websocket_smoke import BufferedConnection, handshake


HTML_BODY = (
    b"<!doctype html><html><head><title>GoreeCloud Owned Fixture</title></head>"
    b'<body><p id="marker">fixture-ok</p></body></html>'
)
EXPECTED_TEXT = "GoreeCloud Owned Fixture|fixture-ok"


class OwnedPageHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.server.paths.append(self.path)  # type: ignore[attr-defined]
        if self.path != "/owned":
            self.send_error(404, "owned fixture only")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(HTML_BODY)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(HTML_BODY)

    def log_message(self, format: str, *args: object) -> None:
        pass


@contextmanager
def owned_http_page() -> Iterator[tuple[str, list[str]]]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), OwnedPageHandler)
    server.paths = []  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True, name="owned-dom-fixture")
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/owned", server.paths  # type: ignore[attr-defined]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def create_target(peer: BufferedConnection, message_id: int, url: str) -> str:
    created = peer.request(message_id, "Target.createTarget", params={"url": url})
    target = created.get("targetId")
    if not isinstance(target, str) or not target:
        raise AssertionError("CDP did not provide an owned test target ID")
    return target


def close_target(peer: BufferedConnection, message_id: int, target: str) -> None:
    closed = peer.request(message_id, "Target.closeTarget", params={"targetId": target})
    if closed.get("success") is not True:
        raise AssertionError("CDP failed to close an owned test target")


def validate_owned_dom(peer: BufferedConnection, url: str) -> None:
    target = create_target(peer, 21, url)
    try:
        session = peer.request(22, "Target.attachToTarget", params={"targetId": target, "flatten": True})
        session_id = session.get("sessionId")
        if not isinstance(session_id, str) or not session_id:
            raise AssertionError("owned HTTP page attach returned no session")

        evaluated = peer.request(
            23,
            "Runtime.evaluate",
            params={
                "expression": 'document.title + "|" + document.querySelector("#marker").textContent',
                "returnByValue": True,
            },
            session_id=session_id,
        )
        result = evaluated.get("result")
        if not isinstance(result, dict) or result.get("type") != "string":
            raise AssertionError("CDP DOM fixture did not yield a string result")
        if result.get("value") != EXPECTED_TEXT:
            raise AssertionError("CDP DOM fixture title/marker did not match the served HTML")
    finally:
        close_target(peer, 24, target)


def main() -> None:
    with owned_http_page() as (url, hits):
        # A normal server is bound only to loopback but has no private-network
        # opt-in, and therefore must not reach even this trusted local page.
        with disposable_cdp_server("goreecloud-headless-browser") as port:
            with handshake(port) as (status, peer):
                if status != 101:
                    raise AssertionError("default-deny CDP connection did not upgrade")
                target = create_target(peer, 19, url)
                close_target(peer, 20, target)
        if hits:
            raise AssertionError("default-deny CDP unexpectedly fetched an owned loopback URL")

        # Opt-in is granted only to a separate fresh runner-local server.
        with disposable_cdp_server("goreecloud-headless-browser", allow_private_network=True) as port:
            with handshake(port) as (status, peer):
                if status != 101:
                    raise AssertionError("opt-in CDP connection did not upgrade")
                validate_owned_dom(peer, url)
        if "/owned" not in hits:
            raise AssertionError("opt-in CDP browser did not fetch the owned HTML fixture")

    print("PASS: default CDP SSRF deny, explicit local-only opt-in, owned HTTP DOM and cleanup")


if __name__ == "__main__":
    main()
