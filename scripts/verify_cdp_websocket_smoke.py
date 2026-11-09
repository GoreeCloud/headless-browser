#!/usr/bin/env python3
"""Bounded, dependency-free RFC6455/CDP smoke against an owned loopback server.

The only evaluated requests are trusted built-in CDP metadata methods.
No remote network interface, page navigation, third-party website or
unreviewed browser payload is involved. This is not a complete WS security test.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import struct
from contextlib import contextmanager
from typing import Iterator

if __package__:
    from .verify_cdp_loopback_smoke import disposable_cdp_server
else:
    from verify_cdp_loopback_smoke import disposable_cdp_server

GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
MAX_HEADER = 16 * 1024
MAX_PAYLOAD = 64 * 1024


def client_frame(payload: bytes, *, opcode: int = 1, mask: bytes | None = None) -> bytes:
    if mask is None:
        mask = os.urandom(4)
    if len(mask) != 4:
        raise ValueError("WebSocket client mask must be four bytes")
    if len(payload) > MAX_PAYLOAD:
        raise ValueError("WebSocket test payload exceeds bound")
    header = bytearray([0x80 | opcode])
    length = len(payload)
    if length < 126:
        header.append(0x80 | length)
    elif length <= 0xFFFF:
        header.extend((0x80 | 126,))
        header.extend(struct.pack("!H", length))
    else:
        header.extend((0x80 | 127,))
        header.extend(struct.pack("!Q", length))
    return bytes(header) + mask + bytes(byte ^ mask[i % 4] for i, byte in enumerate(payload))


class BufferedConnection:
    def __init__(self, stream: socket.socket, pending: bytes = b"") -> None:
        self.stream = stream
        self.pending = pending
        # Callers may raise this *only* for explicitly bounded, owned-fixture
        # binary CDP replies (PDF). The normal metadata smoke remains 64 KiB.
        self.max_response_bytes = MAX_PAYLOAD

    def read_exact(self, length: int) -> bytes:
        if length < 0 or length > self.max_response_bytes + MAX_HEADER:
            raise AssertionError("unexpected length requested from WebSocket peer")
        while len(self.pending) < length:
            part = self.stream.recv(max(1, min(length - len(self.pending), 4096)))
            if not part:
                raise AssertionError("unexpected peer disconnect")
            self.pending += part
        result, self.pending = self.pending[:length], self.pending[length:]
        return result

    def recv_frame(self) -> tuple[int, bytes]:
        first, second = self.read_exact(2)
        if not first & 0x80:
            raise AssertionError("fragmented CDP frames are not covered by the smoke")
        if second & 0x80:
            raise AssertionError("server sent a client-masked frame")
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self.read_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self.read_exact(8))[0]
        if length > self.max_response_bytes:
            raise AssertionError("CDP response exceeded configured test reply budget")
        return first & 0x0F, self.read_exact(length)

    def request(
        self,
        message_id: int,
        method: str,
        *,
        params: dict | None = None,
        session_id: str | None = None,
        expect_error: bool = False,
    ) -> dict:
        request = {"id": message_id, "method": method, "params": params or {}}
        if session_id is not None:
            request["sessionId"] = session_id
        payload = json.dumps(request, separators=(",", ":")).encode()
        self.stream.sendall(client_frame(payload))
        for _ in range(15):
            opcode, body = self.recv_frame()
            if opcode == 0x9:
                self.stream.sendall(client_frame(body, opcode=0xA))
                continue
            if opcode == 0x8:
                raise AssertionError("CDP WebSocket closed before replying")
            if opcode != 0x1:
                raise AssertionError(f"unexpected CDP response opcode: {opcode}")
            response = json.loads(body)
            if response.get("id") == message_id:
                error = response.get("error")
                if expect_error:
                    if not isinstance(error, dict):
                        raise AssertionError(f"CDP {method} unexpectedly succeeded")
                    return error
                if error is not None:
                    raise AssertionError(f"CDP method {method} returned an error")
                result = response.get("result")
                if not isinstance(result, dict):
                    raise AssertionError(f"CDP method {method} returned no result object")
                return result
        raise AssertionError(f"CDP did not answer {method} within 15 frames")


def accept_key(key: bytes) -> str:
    return base64.b64encode(hashlib.sha1(key + GUID).digest()).decode("ascii")


@contextmanager
def handshake(
    port: int,
    *,
    token: str | None = None,
    origin: str | None = None,
    authority: str | None = None,
    ci_note: str | None = None,
) -> Iterator[tuple[int, BufferedConnection]]:
    with socket.create_connection(("127.0.0.1", port), timeout=5) as stream:
        stream.settimeout(8)
        key = base64.b64encode(os.urandom(16))
        header_lines = [
            "GET /devtools/browser HTTP/1.1",
            f"Host: {authority or f'127.0.0.1:{port}'}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {key.decode('ascii')}",
            "Sec-WebSocket-Version: 13",
        ]
        if ci_note is not None:
            if any(c in ci_note for c in "\r\n"):
                raise ValueError("CI WebSocket note must not contain line breaks")
            header_lines.append(f"X-GoreeCloud-Test-Note: {ci_note}")
        if token is not None:
            header_lines.append(f"Authorization: Bearer {token}")
        if origin is not None:
            header_lines.append(f"Origin: {origin}")
        request = ("\r\n".join(header_lines) + "\r\n\r\n").encode("ascii")
        stream.sendall(request)
        head = bytearray()
        while b"\r\n\r\n" not in head:
            piece = stream.recv(4096)
            if not piece:
                raise AssertionError("CDP closed connection before handshake response")
            head.extend(piece)
            if len(head) > MAX_HEADER:
                raise AssertionError("oversized WebSocket handshake response")
        raw_head, pending = bytes(head).split(b"\r\n\r\n", 1)
        lines = raw_head.decode("latin1").split("\r\n")
        parts = lines[0].split(" ", 2)
        if len(parts) < 2 or not parts[0].startswith("HTTP/"):
            raise AssertionError("malformed WebSocket HTTP status")
        status = int(parts[1])
        response_headers = {}
        for line in lines[1:]:
            if ":" not in line:
                raise AssertionError("malformed WebSocket HTTP header")
            name, value = line.split(":", 1)
            response_headers[name.lower()] = value.strip()
        if status == 101:
            if response_headers.get("sec-websocket-accept") != accept_key(key):
                raise AssertionError("WebSocket handshake accept key mismatch")
            if response_headers.get("upgrade", "").lower() != "websocket":
                raise AssertionError("missing WebSocket upgrade confirmation")
        yield status, BufferedConnection(stream, pending)


def require_handshake_refused(port: int, expected: int, **kwargs: str) -> None:
    with handshake(port, **kwargs) as (status, _):
        if status != expected:
            raise AssertionError(f"expected WebSocket HTTP {expected} refusal; got {status}")


def verify_browser_metadata(peer: BufferedConnection) -> None:
    version = peer.request(1, "Browser.getVersion")
    if version.get("protocolVersion") != "1.3":
        raise AssertionError("CDP WebSocket Browser.getVersion protocol mismatch")
    if not version.get("product", "").startswith("Chrome/"):
        raise AssertionError("CDP WebSocket Browser.getVersion missing product")
    targets = peer.request(2, "Target.getTargets")
    if not isinstance(targets.get("targetInfos"), list):
        raise AssertionError("CDP WebSocket Target.getTargets did not return an array")

    # A harmless parameter string must not be mistaken for a real shutdown.
    peer.request(3, "Network.enable", params={"note": "Browser.close"})
    if peer.request(4, "Browser.getVersion").get("protocolVersion") != "1.3":
        raise AssertionError("CDP session was closed by non-close parameter")


def main() -> None:
    with disposable_cdp_server("goreecloud-headless-browser") as port:
        require_handshake_refused(port, 403, origin="https://untrusted.invalid")
        with handshake(port) as (status, peer):
            if status != 101:
                raise AssertionError(f"CDP WS upgrade refused local native client (HTTP {status})")
            verify_browser_metadata(peer)
    print("PASS: GoreeCloud native loopback WebSocket upgrade, metadata and browser-Origin block")

    # Token is ephemeral and kept out of command arguments, logs, and output.
    import secrets

    token = secrets.token_urlsafe(32)
    with disposable_cdp_server("obscura", token) as port:
        require_handshake_refused(port, 401)
        require_handshake_refused(port, 401, token="incorrect-bearer")
        require_handshake_refused(port, 403, token=token, origin="https://untrusted.invalid")
        with handshake(port, token=token) as (status, peer):
            if status != 101:
                raise AssertionError(f"authenticated CDP WS upgrade failed (HTTP {status})")
            verify_browser_metadata(peer)
    print("PASS: Obscura compatibility WebSocket bearer token and CDP metadata")


if __name__ == "__main__":
    main()
