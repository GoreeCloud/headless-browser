#!/usr/bin/env python3
"""Bounded real WebSocket inbound-frame refusal on owned loopback only.

Only a masked frame HEADER declaring an over-budget length is sent. No
untrusted payload, external connection or large allocation is necessary.
"""

from __future__ import annotations

import os
import socket
import struct

if __package__:
    from .verify_cdp_loopback_smoke import disposable_cdp_server
    from .verify_cdp_websocket_smoke import handshake
else:
    from verify_cdp_loopback_smoke import disposable_cdp_server
    from verify_cdp_websocket_smoke import handshake

MAX_CDP_INBOUND_MESSAGE_BYTES = 16 * 1024 * 1024


def oversized_masked_header(mask: bytes) -> bytes:
    if len(mask) != 4:
        raise ValueError("masked frame header requires a four-byte client mask")
    return b"\x81\xff" + struct.pack("!Q", MAX_CDP_INBOUND_MESSAGE_BYTES + 1) + mask


def assert_oversized_frame_rejected(port: int) -> None:
    with handshake(port) as (status, peer):
        if status != 101:
            raise AssertionError("owned-loopback websocket did not upgrade")
        peer.stream.settimeout(6)
        peer.stream.sendall(oversized_masked_header(os.urandom(4)))
        # A frame length over the configured cap is invalid before any body
        # is consumed. Tungstenite may send a close frame or close the socket.
        try:
            response = peer.stream.recv(64)
        except (ConnectionResetError, BrokenPipeError):
            response = b""
        except socket.timeout as error:
            raise AssertionError("oversized WebSocket header was not rejected promptly") from error
        if response and (response[0] & 0x0F) != 0x08:
            raise AssertionError("oversized WebSocket frame received an unexpected non-close reply")

    # A malformed client must not terminate the underlying CDP listener.
    with handshake(port) as (status, peer):
        if status != 101:
            raise AssertionError("CDP listener failed after oversized client frame")
        result = peer.request(31, "Browser.getVersion")
        if result.get("protocolVersion") != "1.3":
            raise AssertionError("CDP listener failed protocol metadata after oversized client frame")


def main() -> None:
    with disposable_cdp_server("goreecloud-headless-browser") as port:
        assert_oversized_frame_rejected(port)
    print("PASS: oversized masked WebSocket request rejected; loopback CDP remains usable")


if __name__ == "__main__":
    main()
