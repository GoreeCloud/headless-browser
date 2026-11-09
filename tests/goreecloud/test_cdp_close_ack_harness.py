"""Offline protocol tests for Browser.close acknowledgment and session identity."""

import unittest

from scripts import verify_cdp_close_ack_smoke as smoke


class CloseAckTests(unittest.TestCase):
    def test_exact_success_reply(self):
        smoke.validate_close_reply(
            {"id": smoke.CLOSE_ID, "result": {}, "sessionId": smoke.SESSION_ID}
        )

    def test_wrong_request_id_rejected(self):
        with self.assertRaisesRegex(AssertionError, "identity"):
            smoke.validate_close_reply(
                {"id": smoke.CLOSE_ID + 1, "result": {}, "sessionId": smoke.SESSION_ID}
            )

    def test_missing_session_identity_rejected(self):
        with self.assertRaisesRegex(AssertionError, "session ID"):
            smoke.validate_close_reply({"id": smoke.CLOSE_ID, "result": {}})

    def test_nonempty_result_rejected(self):
        with self.assertRaisesRegex(AssertionError, "success result"):
            smoke.validate_close_reply({
                "id": smoke.CLOSE_ID, "result": {"stale": True},
                "sessionId": smoke.SESSION_ID,
            })

    def test_error_response_rejected(self):
        with self.assertRaisesRegex(AssertionError, "error"):
            smoke.validate_close_reply({
                "id": smoke.CLOSE_ID, "result": {},
                "sessionId": smoke.SESSION_ID, "error": {"code": -1},
            })

    def test_nonobject_rejected(self):
        with self.assertRaisesRegex(AssertionError, "JSON object"):
            smoke.validate_close_reply([])


if __name__ == "__main__":
    unittest.main()
