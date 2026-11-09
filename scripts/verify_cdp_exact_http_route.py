#!/usr/bin/env python3
"""Exact CDP discovery-target routing on a disposable owned-loopback server.

This checks that injected '/json/version' strings in unrelated WebSocket
headers do not transform a native CDP handshake into HTTP discovery.
No remote websites or public network listeners are used.
"""

from __future__ import annotations

import http.client
import json

if __package__:
    from .verify_cdp_loopback_smoke import disposable_cdp_server
    from .verify_cdp_websocket_smoke import handshake
else:
    from verify_cdp_loopback_smoke import disposable_cdp_server
    from verify_cdp_websocket_smoke import handshake


def request_status(port: int, path: str) -> tuple[int | None, bytes]:
    if not path.startswith("/") or path.startswith("//") or any(ch in path for ch in ("\r", "\n")):
        raise ValueError("test HTTP path must be a bounded relative target")
    if len(path) > 200:
        raise ValueError("test HTTP target is too long")
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", path, headers={"Host": f"127.0.0.1:{port}"})
        response = connection.getresponse()
        return response.status, response.read(64 * 1024)
    except (http.client.RemoteDisconnected, ConnectionResetError, BrokenPipeError):
        return None, b""
    finally:
        connection.close()


def validate_exact_routing(port: int) -> None:
    status, body = request_status(port, "/json/version?hint=/json/list")
    if status != 200 or not json.loads(body).get("webSocketDebuggerUrl", "").endswith("/devtools/browser"):
        raise AssertionError("valid CDP discovery endpoint query changed")

    # Header hints and query substrings may never override the request path.
    with handshake(port, ci_note="/json/version") as (status, peer):
        if status != 101:
            raise AssertionError("WebSocket request was misrouted due to an unrelated header")
        result = peer.request(91, "Browser.getVersion")
        if result.get("protocolVersion") != "1.3":
            raise AssertionError("CDP WebSocket did not survive unrelated discovery header")

    # Exact route matching must not accept a near-miss URL as JSON discovery.
    status, _ = request_status(port, "/json/version-overlong")
    if status == 200:
        raise AssertionError("CDP discovery accepted a lookalike path")


def main() -> None:
    with disposable_cdp_server("goreecloud-headless-browser") as port:
        validate_exact_routing(port)
    print("PASS: CDP discovery routes match only HTTP request paths; WebSocket header hints are safe")


if __name__ == "__main__":
    main()
