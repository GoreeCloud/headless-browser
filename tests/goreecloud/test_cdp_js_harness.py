"""Stub-only regression tests for the trusted, no-navigation CDP smoke."""

import unittest

from scripts.verify_cdp_js_loopback_smoke import check_trusted_blank_page


class FixturePeer:
    def __init__(self, overrides=None):
        self.calls = []
        self.replies = {
            10: {"code": -32000, "message": "file:// target disabled"},
            11: {"targetId": "page-test"},
            12: {"sessionId": "page-session"},
            13: {"result": {"type": "number", "value": 42}},
            16: {"result": {"type": "object", "value": {"__init": True, "note": "Browser.close"}}},
            14: {"success": True},
            15: {"targetInfos": []},
        }
        self.replies.update(overrides or {})

    def request(self, message_id, method, *, params=None, session_id=None, expect_error=False):
        self.calls.append((message_id, method, params, session_id, expect_error))
        return self.replies[message_id]


class BlankPageSmokeTests(unittest.TestCase):
    def test_trusted_about_blank_lifecycle_and_cleanup(self):
        peer = FixturePeer()
        check_trusted_blank_page(peer)
        self.assertEqual([call[1] for call in peer.calls], [
            "Target.createTarget",
            "Target.createTarget",
            "Target.attachToTarget",
            "Runtime.evaluate",
            "Runtime.evaluate",
            "Target.closeTarget",
            "Target.getTargets",
        ])
        self.assertTrue(peer.calls[0][-1])
        self.assertEqual(peer.calls[0][2]["url"], "file:///tmp/goreecloud-file-access-must-remain-disabled.html")
        self.assertEqual(peer.calls[1][2], {"url": "about:blank"})
        self.assertEqual(peer.calls[3][2]["expression"], "6 * 7")
        self.assertEqual(peer.calls[3][3], "page-session")

    def test_file_scheme_guard_must_refuse_navigation(self):
        with self.assertRaisesRegex(AssertionError, "file://"):
            check_trusted_blank_page(FixturePeer({10: {"code": 0, "message": "accepted"}}))

    def test_target_creation_requires_nonempty_id(self):
        with self.assertRaisesRegex(AssertionError, "target identity"):
            check_trusted_blank_page(FixturePeer({11: {"targetId": ""}}))

    def test_attachment_requires_session_id(self):
        with self.assertRaisesRegex(AssertionError, "session identity"):
            check_trusted_blank_page(FixturePeer({12: {"sessionId": None}}))

    def test_runtime_must_return_exact_arithmetic_value(self):
        with self.assertRaisesRegex(AssertionError, "return 42"):
            check_trusted_blank_page(FixturePeer({13: {"result": {"type": "number", "value": 41}}}))

    def test_runtime_must_report_number_type(self):
        with self.assertRaisesRegex(AssertionError, "numeric result"):
            check_trusted_blank_page(FixturePeer({13: {"result": {"type": "string", "value": 42}}}))

    def test_nested_user_init_field_must_be_delivered(self):
        with self.assertRaisesRegex(AssertionError, "user __init data"):
            check_trusted_blank_page(FixturePeer({16: {"result": {"value": {"__init": False}}}}))

    def test_target_cleanup_must_succeed(self):
        with self.assertRaisesRegex(AssertionError, "closed cleanly"):
            check_trusted_blank_page(FixturePeer({14: {"success": False}}))

    def test_closed_target_must_not_remain_visible(self):
        with self.assertRaisesRegex(AssertionError, "still appears active"):
            check_trusted_blank_page(FixturePeer({
                15: {"targetInfos": [{"targetId": "page-test"}]},
            }))


if __name__ == "__main__":
    unittest.main()
