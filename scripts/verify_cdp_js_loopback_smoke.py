#!/usr/bin/env python3
"""Actual CDP about:blank page lifecycle and trusted V8 expression smoke.

Runs only in a disposable CI runner on a local 127.0.0.1 server.
The only evaluated JavaScript is a literal arithmetic expression. No
external navigation, arbitrary pages, downloads, profiling or host files.
"""

from __future__ import annotations

if __package__:
    from .verify_cdp_loopback_smoke import disposable_cdp_server
    from .verify_cdp_websocket_smoke import BufferedConnection, handshake
else:
    from verify_cdp_loopback_smoke import disposable_cdp_server
    from verify_cdp_websocket_smoke import BufferedConnection, handshake


def check_trusted_blank_page(peer: BufferedConnection) -> None:
    # Detect a file-navigation bypass without ever specifying a real system
    # file. This deliberately non-existent URL must be refused in the CDP
    # target layer before it is ever sent to a filesystem/network loader.
    denied = peer.request(
        10, "Target.createTarget",
        params={"url": "file:///tmp/goreecloud-file-access-must-remain-disabled.html"},
        expect_error=True,
    )
    if "file://" not in str(denied.get("message", "")):
        raise AssertionError("CDP file:// target was not rejected by the intended guard")

    opened = peer.request(11, "Target.createTarget", params={"url": "about:blank"})
    target_id = opened.get("targetId")
    if not isinstance(target_id, str) or not target_id:
        raise AssertionError("about:blank target creation returned no target identity")

    attached = peer.request(
        12, "Target.attachToTarget",
        params={"targetId": target_id, "flatten": True},
    )
    session = attached.get("sessionId")
    if not isinstance(session, str) or not session:
        raise AssertionError("CDP did not return a page session identity")

    evaluated = peer.request(
        13, "Runtime.evaluate",
        params={"expression": "6 * 7", "returnByValue": True},
        session_id=session,
    )
    result = evaluated.get("result")
    if not isinstance(result, dict) or result.get("value") != 42:
        raise AssertionError("trusted about:blank V8 evaluation did not return 42")
    if result.get("type") != "number":
        raise AssertionError("CDP Runtime.evaluate did not report a numeric result")

    # A nested __init field is legitimate user data and must not be swallowed
    # by the server's private connection-initialization envelope filter.
    nested = peer.request(
        16, "Runtime.evaluate",
        params={"expression": "({__init: true, note: 'Browser.close'})", "returnByValue": True},
        session_id=session,
    )
    value = nested.get("result", {}).get("value")
    if value != {"__init": True, "note": "Browser.close"}:
        raise AssertionError("CDP response containing user __init data was lost or corrupted")

    closed = peer.request(14, "Target.closeTarget", params={"targetId": target_id})
    if closed.get("success") is not True:
        raise AssertionError("about:blank target was not closed cleanly")
    remaining = peer.request(15, "Target.getTargets").get("targetInfos")
    if not isinstance(remaining, list):
        raise AssertionError("CDP did not report remaining target identities")
    if any(target.get("targetId") == target_id for target in remaining if isinstance(target, dict)):
        raise AssertionError("closed about:blank target still appears active")


def main() -> None:
    with disposable_cdp_server("goreecloud-headless-browser") as port:
        with handshake(port) as (status, peer):
            if status != 101:
                raise AssertionError(f"owned-loopback CDP websocket refused upgrade (HTTP {status})")
            check_trusted_blank_page(peer)
    print("PASS: owned-loopback CDP rejects file://, creates and closes about:blank, evaluates trusted JS")


if __name__ == "__main__":
    main()
