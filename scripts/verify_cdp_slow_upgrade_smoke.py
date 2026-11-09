#!/usr/bin/env python3
"""Refuse incomplete WebSocket upgrades on an owned loopback CDP listener.

A malformed request line with a valid Host header is intentionally sent
without the terminating CRLFCRLF. Neither a public listener nor any external
URL, untrusted site, large payload or privileged process is used.
"""

from __future__ import annotations

import socket
import time

if __package__:
    from .verify_cdp_loopback_smoke import disposable_cdp_server
    from .verify_cdp_websocket_smoke import handshake
else:
    from verify_cdp_loopback_smoke import disposable_cdp_server
    from verify_cdp_websocket_smoke import handshake


def incomplete_upgrade_request(port: int) -> bytes:
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("owned-loopback test port must be an integer in 1..65535")
    head = (
        f"POST /devtools/browser HTTP/1.1\r\n"
        f"Host: 127.0.0.1:{port}\r\n"
        "X-GoreeCloud-Fixture: never-ending"
    ).encode("ascii")
    if b"\r\n\r\n" in head or not head.startswith(b"POST "):
        raise AssertionError("test must send only an incomplete, non-GET request head")
    return head


def check_upgrade_deadline(binary: str) -> None:
    with disposable_cdp_server(binary, max_connections=1) as port:
        with socket.create_connection(("127.0.0.1", port), timeout=5) as stalled:
            stalled.settimeout(9)
            stalled.sendall(incomplete_upgrade_request(port))
            # Allow the dedicated I/O task to reserve its CDP connection slot.
            time.sleep(0.4)
            with handshake(port) as (status, _peer):
                if status != 503:
                    raise AssertionError(
                        f"incomplete upgrade did not reserve the single slot (HTTP {status})"
                    )

            started = time.monotonic()
            try:
                # An incomplete upgrade must not wait forever for missing HTTP
                # terminators, and must close before the nine-second deadline.
                data = stalled.recv(4096)
            except (ConnectionResetError, BrokenPipeError):
                data = b""
            except socket.timeout as exc:
                raise AssertionError("incomplete WebSocket upgrade never timed out") from exc
            if data:
                raise AssertionError("unexpected response instead of failed incomplete upgrade")
            if time.monotonic() - started > 8.5:
                raise AssertionError("WebSocket upgrade did not terminate within deadline budget")

        # The reserved slot must be released after the handshake times out.
        end = time.monotonic() + 5
        while True:
            with handshake(port) as (status, peer):
                if status == 101:
                    result = peer.request(41, "Browser.getVersion")
                    if result.get("protocolVersion") != "1.3":
                        raise AssertionError("CDP listener was unhealthy after slow handshake")
                    break
                if status != 503:
                    raise AssertionError(f"unexpected CDP recovery handshake HTTP {status}")
            if time.monotonic() >= end:
                raise AssertionError("WebSocket handshake timeout did not release the CDP slot")
            time.sleep(0.1)


def main() -> None:
    for name in ("goreecloud-headless-browser", "obscura"):
        check_upgrade_deadline(name)
        print(f"PASS: {name} rejects slow incomplete WebSocket upgrade and recovers its client slot")


if __name__ == "__main__":
    main()
