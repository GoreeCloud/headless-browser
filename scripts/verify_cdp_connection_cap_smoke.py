#!/usr/bin/env python3
"""Bounded single-slot CDP WebSocket admission and liveness smoke.

Runs only against disposable 127.0.0.1 native development binaries.
No real web navigation, external connections or publishing.
"""

from __future__ import annotations

import time

if __package__:
    from .verify_cdp_loopback_smoke import disposable_cdp_server
    from .verify_cdp_websocket_smoke import BufferedConnection, handshake
else:
    from verify_cdp_loopback_smoke import disposable_cdp_server
    from verify_cdp_websocket_smoke import BufferedConnection, handshake


def assert_version(peer: BufferedConnection, request_id: int) -> None:
    value = peer.request(request_id, "Browser.getVersion")
    if value.get("protocolVersion") != "1.3":
        raise AssertionError("existing CDP client lost version protocol while at capacity")


def verify_single_slot(binary: str) -> None:
    # --max-connections 1 limits *live WS clients*; discovery HTTP is separate.
    with disposable_cdp_server(binary, max_connections=1) as port:
        with handshake(port) as (status, peer):
            if status != 101:
                raise AssertionError(f"first {binary} CDP client did not connect (HTTP {status})")
            assert_version(peer, 1)

            with handshake(port) as (refused, _):
                if refused != 503:
                    raise AssertionError(
                        f"expected 503 CDP connection cap, received HTTP {refused}"
                    )

            # Refusing an extra client must not take down or poison the
            # existing authorized connection.
            assert_version(peer, 2)

        # Slot accounting must recover after the incumbent disconnects.
        # Release happens asynchronously in the per-connection thread.
        deadline = time.monotonic() + 5.0
        while True:
            with handshake(port) as (status, successor):
                if status == 101:
                    assert_version(successor, 3)
                    break
                if status != 503:
                    raise AssertionError(f"unexpected reconnect HTTP status {status}")
            if time.monotonic() >= deadline:
                raise AssertionError("CDP connection slot was not released after client disconnect")
            time.sleep(0.1)


def main() -> None:
    for binary in ("goreecloud-headless-browser", "obscura"):
        verify_single_slot(binary)
        print(f"PASS: {binary} enforces one live CDP WebSocket without dropping incumbent")


if __name__ == "__main__":
    main()
