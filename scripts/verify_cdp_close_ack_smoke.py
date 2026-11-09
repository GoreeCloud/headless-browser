#!/usr/bin/env python3
"""Verify that native Browser.close acknowledges before closing its WebSocket.

Uses an ephemeral owned-loopback CDP server. Never visits external websites.
"""

from __future__ import annotations

import json
import socket

if __package__:
    from .verify_cdp_loopback_smoke import disposable_cdp_server
    from .verify_cdp_websocket_smoke import client_frame, handshake
else:
    from verify_cdp_loopback_smoke import disposable_cdp_server
    from verify_cdp_websocket_smoke import client_frame, handshake

CLOSE_ID = 71
SESSION_ID = "owned-close-test-session"


def validate_close_reply(message: object) -> None:
    if not isinstance(message, dict):
        raise AssertionError("Browser.close reply was not a JSON object")
    if message.get("id") != CLOSE_ID or message.get("result") != {}:
        raise AssertionError("Browser.close reply lost its request identity or success result")
    if message.get("sessionId") != SESSION_ID:
        raise AssertionError("Browser.close reply lost its original session ID")
    if "error" in message:
        raise AssertionError("Browser.close unexpectedly returned an error")


def assert_close_acknowledged(port: int) -> None:
    with handshake(port) as (status, peer):
        if status != 101:
            raise AssertionError("owned-loopback CDP WebSocket upgrade failed")
        request = json.dumps(
            {"id": CLOSE_ID, "method": "Browser.close", "sessionId": SESSION_ID},
            separators=(",", ":"),
        ).encode("utf-8")
        peer.stream.sendall(client_frame(request))
        acknowledged = False
        for _ in range(8):
            opcode, payload = peer.recv_frame()
            if opcode == 0x8:
                raise AssertionError("CDP closed WebSocket before Browser.close acknowledgment")
            if opcode == 0x9:
                peer.stream.sendall(client_frame(payload, opcode=0xA))
                continue
            if opcode != 0x1:
                raise AssertionError("unexpected CDP WebSocket frame before close acknowledgment")
            reply = json.loads(payload)
            if reply.get("id") == CLOSE_ID:
                validate_close_reply(reply)
                acknowledged = True
                break
        if not acknowledged:
            raise AssertionError("Browser.close acknowledgment was not received")
        peer.stream.settimeout(4)
        # A clean WebSocket close frame is preferred. A prompt TCP EOF is
        # tolerated, but continuing to accept frames or idling is not.
        try:
            opcode, _payload = peer.recv_frame()
        except (AssertionError, ConnectionResetError, BrokenPipeError):
            pass
        except socket.timeout as error:
            raise AssertionError("Browser.close did not terminate the WebSocket promptly") from error
        else:
            if opcode != 0x8:
                raise AssertionError("Browser.close connection emitted a non-close frame")

    # Browser.close terminates this client connection, not the CDP server.
    with handshake(port) as (status, peer):
        if status != 101:
            raise AssertionError("CDP server did not recover after Browser.close")
        if peer.request(72, "Browser.getVersion").get("protocolVersion") != "1.3":
            raise AssertionError("CDP server could not serve a fresh client after Browser.close")


def main() -> None:
    with disposable_cdp_server("goreecloud-headless-browser") as port:
        assert_close_acknowledged(port)
    print("PASS: Browser.close acknowledged with session identity, WebSocket shut down, listener recovered")


if __name__ == "__main__":
    main()
