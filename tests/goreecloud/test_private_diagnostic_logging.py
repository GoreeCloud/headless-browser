"""Guard targeted GoreeShield log data minimization against regressions.

Source-level checks only: not a proof that arbitrary upstream error strings
or all logging dependencies cannot emit personal information.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def source(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class PrivateDiagnosticLoggingTests(unittest.TestCase):
    def test_cdp_interception_omits_raw_urls_and_request_ids(self):
        data = source("crates/obscura-cdp/src/server.rs")
        for unsafe in (
            "requestPaused for {} {} (sending to client)",
            "INTERCEPTION resolution: {} for {}, paused_count={}",
            "INTERCEPTION resolved: {}",
        ):
            with self.subTest(unsafe=unsafe):
                self.assertNotIn(unsafe, data)
        self.assertIn("INTERCEPTION: requestPaused for {} (URL redacted", data)
        self.assertIn("INTERCEPTION resolved (request ID redacted)", data)

    def test_browser_and_cookie_logs_redact_paths_and_sources(self):
        page = source("crates/obscura-browser/src/page.rs")
        cookie = source("crates/obscura-browser/src/context.rs")
        for variable in ("frame.url", "frame_url", "full_url", "requested_url",
                         "import_url", "execution_url"):
            with self.subTest(variable=variable):
                self.assertNotRegex(
                    page,
                    r"tracing::(?:info|debug|warn|error)!\([^;]{0,250}\b"
                    + re.escape(variable)
                    + r"\b[^;]{0,250}\);",
                )
        self.assertNotRegex(
            cookie, r"tracing::(?:info|warn|debug|error)!\([^;]*cookie_path\.display\(\)",
        )
        self.assertGreaterEqual(page.count("URL redacted"), 15)
        self.assertNotIn('module = %full_url', page)
        self.assertNotIn('module = url.as_deref()', page)
        self.assertNotIn('"Refusing to execute script {} after HTTP {}"', page)
        self.assertGreaterEqual(cookie.count("path redacted"), 4)

    def test_url_tokens_are_not_explicit_fields_in_network_logs(self):
        for path in ("crates/obscura-net/src/client.rs",
                     "crates/obscura-net/src/wreq_client.rs"):
            content = source(path)
            with self.subTest(path=path):
                self.assertNotIn('tracing::debug!("Blocked tracker: {}",', content)
                self.assertNotIn("tracing::debug!(%url,", content)
                self.assertIn("URL redacted", content)

    def test_page_console_messages_and_eval_text_are_not_server_log_payloads(self):
        page = source("crates/obscura-browser/src/page.rs")
        ops = source("crates/obscura-js/src/ops.rs")
        for leak in (
            "JS eval error/timeout for",
            "JS eval error for",
            "truncate_on_char_boundary(expression",
            'tracing::debug!("evaluate_for_cdp error: {}", e)',
            'tracing::debug!("callFunctionOn error: {}", e)',
        ):
            with self.subTest(leak=leak):
                self.assertNotIn(leak, page)
        self.assertIn("JS evaluation failed (details redacted)", page)
        self.assertIn("CDP function call error (details redacted)", page)
        self.assertIn("Page console message redacted", ops)
        self.assertIn("message_bytes = msg.len()", ops)
        for level in ("tracing::warn!", "tracing::error!", "tracing::info!"):
            with self.subTest(level=level):
                self.assertNotIn(f'{level}(target: "obscura::console", "{{}}", msg)', ops)
        # CDP console events retain their original arguments; buffered text
        # now uses explicit bounded retention rather than an unrestricted copy.
        self.assertIn(
            "push_bounded_console_message(&mut page.pending_console_messages, level, msg)",
            ops,
        )
        self.assertIn("if !page.runtime_events_enabled", ops)
        self.assertIn("RuntimeEvent::Console(RuntimeConsoleEvent", ops)

    def test_js_resource_logs_omit_unmasked_url_fields(self):
        ops = source("crates/obscura-js/src/ops.rs")
        runtime = source("crates/obscura-js/src/runtime.rs")
        self.assertNotIn("op_fetch_url completed: {} {} ({} bytes)", ops)
        self.assertNotIn("op_fetch_url called: {} {} (intercept check pending)", ops)
        self.assertNotIn("url = %load.url,", runtime)
        self.assertNotIn("tracing::debug!(url = %load.url,", runtime)
        self.assertIn("op_fetch_url completed: {} (URL redacted", ops)
        self.assertGreaterEqual(runtime.count("URL redacted"), 3)


if __name__ == "__main__":
    unittest.main()
