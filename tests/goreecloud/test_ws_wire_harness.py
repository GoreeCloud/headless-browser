"""Dependency-free RFC6455 smoke harness correctness and bounds tests."""

import base64
import json
import socket
import struct
import unittest

from scripts import verify_cdp_websocket_smoke as ws


class WebSocketWireTests(unittest.TestCase):
    def test_known_rfc6455_accept_digest(self):
        key = b"dGhlIHNhbXBsZSBub25jZQ=="
        self.assertEqual(ws.accept_key(key), "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=")

    def test_masked_client_text_frame(self):
        data = b"hello"
        frame = ws.client_frame(data, mask=bytes([0x37, 0xFA, 0x21, 0x3D]))
        self.assertEqual(frame[:2], bytes([0x81, 0x80 | len(data)]))
        self.assertEqual(frame[2:6], bytes([0x37, 0xFA, 0x21, 0x3D]))
        decoded = bytes(value ^ frame[2 + (i % 4)] for i, value in enumerate(frame[6:]))
        self.assertEqual(decoded, data)

    def test_extended_client_length_and_pong_opcode(self):
        payload = b"x" * 126
        frame = ws.client_frame(payload, opcode=0xA, mask=b"abcd")
        self.assertEqual(frame[0], 0x8A)
        self.assertEqual(frame[1], 0xFE)
        self.assertEqual(struct.unpack("!H", frame[2:4])[0], 126)
        self.assertEqual(frame[4:8], b"abcd")

    def test_bad_client_mask_rejected(self):
        with self.assertRaisesRegex(ValueError, "four bytes"):
            ws.client_frame(b"test", mask=b"bad")

    def test_oversize_client_payload_refused(self):
        with self.assertRaisesRegex(ValueError, "exceeds bound"):
            ws.client_frame(b"x" * (ws.MAX_PAYLOAD + 1))

    def test_receives_unmasked_server_text_frame(self):
        left, right = socket.socketpair()
        try:
            left.settimeout(2)
            right.sendall(b"\x81\x05hello")
            conn = ws.BufferedConnection(left, b"")
            self.assertEqual(conn.recv_frame(), (1, b"hello"))
        finally:
            left.close()
            right.close()

    def test_server_masked_frame_is_rejected(self):
        left, right = socket.socketpair()
        try:
            right.sendall(b"\x81\x80")
            with self.assertRaisesRegex(AssertionError, "client-masked"):
                ws.BufferedConnection(left).recv_frame()
        finally:
            left.close()
            right.close()

    def test_server_oversized_frame_is_rejected_before_reading_body(self):
        left, right = socket.socketpair()
        try:
            right.sendall(b"\x81\x7f" + struct.pack("!Q", ws.MAX_PAYLOAD + 1))
            with self.assertRaisesRegex(AssertionError, "exceeded"):
                ws.BufferedConnection(left).recv_frame()
        finally:
            left.close()
            right.close()

    def test_server_fragmented_frame_rejected(self):
        left, right = socket.socketpair()
        try:
            right.sendall(b"\x01\x00")
            with self.assertRaisesRegex(AssertionError, "fragmented"):
                ws.BufferedConnection(left).recv_frame()
        finally:
            left.close()
            right.close()

    def test_cdp_result_validation(self):
        left, right = socket.socketpair()
        try:
            result = json.dumps({"id": 1, "result": {"protocolVersion": "1.3", "product": "Chrome/145"}}).encode()
            right.sendall(bytes([0x81, len(result)]) + result)
            peer = ws.BufferedConnection(left)
            self.assertEqual(peer.request(1, "Browser.getVersion")["protocolVersion"], "1.3")
        finally:
            left.close()
            right.close()


if __name__ == "__main__":
    unittest.main()
