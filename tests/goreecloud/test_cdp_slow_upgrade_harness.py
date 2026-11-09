"""Offline tests for the private incomplete-upgrade CDP fixture."""

import unittest

from scripts.verify_cdp_slow_upgrade_smoke import incomplete_upgrade_request


class SlowUpgradeHarnessTests(unittest.TestCase):
    def test_incomplete_non_get_contains_correct_bound_authority(self):
        head = incomplete_upgrade_request(49231)
        self.assertEqual(head.split(b"\r\n")[0], b"POST /devtools/browser HTTP/1.1")
        self.assertIn(b"Host: 127.0.0.1:49231\r\n", head)
        self.assertNotIn(b"\r\n\r\n", head)
        self.assertLess(len(head), 256)

    def test_untrusted_port_values_are_rejected_before_socket_use(self):
        for port in (0, -1, 65536, True, "1234", 2.4, None):
            with self.subTest(port=port), self.assertRaisesRegex(ValueError, "integer"):
                incomplete_upgrade_request(port)

    def test_valid_boundary_ports_preserve_exact_authority(self):
        for port in (1, 65535):
            head = incomplete_upgrade_request(port)
            self.assertIn(f"Host: 127.0.0.1:{port}\r\n".encode("ascii"), head)
            self.assertNotIn(b"\r\n\r\n", head)


if __name__ == "__main__":
    unittest.main()
