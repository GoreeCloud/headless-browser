"""No-network smoke regression tests for the CDP single-slot admission harness."""

import unittest
from contextlib import contextmanager
from unittest import mock

from scripts import verify_cdp_connection_cap_smoke as gate


class Client:
    def __init__(self, broken=False):
        self.ids = []
        self.broken = broken

    def request(self, request_id, method):
        self.ids.append(request_id)
        if self.broken:
            return {"protocolVersion": "0.0"}
        return {"protocolVersion": "1.3"}


class ConnectionCapHarnessTests(unittest.TestCase):
    def test_admits_first_refuses_second_and_keeps_first_usable(self):
        first = Client()
        slots = []
        successor = Client()

        @contextmanager
        def start(name, *, max_connections):
            self.assertEqual(name, "goreecloud-headless-browser")
            self.assertEqual(max_connections, 1)
            yield 49999

        @contextmanager
        def handshake(port):
            self.assertEqual(port, 49999)
            number = len(slots)
            slots.append(number)
            if number == 0:
                yield 101, first
            elif number == 1:
                yield 503, Client()
            else:
                yield 101, successor

        with mock.patch.object(gate, "disposable_cdp_server", start), mock.patch.object(
            gate, "handshake", handshake
        ):
            gate.verify_single_slot("goreecloud-headless-browser")

        self.assertEqual(slots, [0, 1, 2])
        self.assertEqual(first.ids, [1, 2])
        self.assertEqual(successor.ids, [3])

    def test_accepting_second_connection_fails_closed(self):
        @contextmanager
        def start(_name, *, max_connections):
            self.assertEqual(max_connections, 1)
            yield 49000

        @contextmanager
        def handshake(_port):
            yield 101, Client()

        with mock.patch.object(gate, "disposable_cdp_server", start), mock.patch.object(
            gate, "handshake", handshake
        ):
            with self.assertRaisesRegex(AssertionError, "expected 503"):
                gate.verify_single_slot("obscura")

    def test_incumbent_liveness_must_be_preserved(self):
        class FailsSecondRequest(Client):
            def request(self, request_id, method):
                self.ids.append(request_id)
                return {"protocolVersion": "1.3" if request_id == 1 else "0.0"}

        live = FailsSecondRequest()
        handshakes = []

        @contextmanager
        def start(_name, *, max_connections):
            self.assertEqual(max_connections, 1)
            yield 49000

        @contextmanager
        def handshake(_port):
            handshakes.append(len(handshakes))
            yield (101, live) if len(handshakes) == 1 else (503, Client())

        with mock.patch.object(gate, "disposable_cdp_server", start), mock.patch.object(
            gate, "handshake", handshake
        ):
            with self.assertRaisesRegex(AssertionError, "lost version protocol"):
                gate.verify_single_slot("obscura")
        self.assertEqual(live.ids, [1, 2])


if __name__ == "__main__":
    unittest.main()
