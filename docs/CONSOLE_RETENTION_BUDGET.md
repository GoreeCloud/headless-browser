# In-memory console text retention budgets

**Status:** Development-source Wardveil memory and GoreeShield data-minimization control. Not proof of total process memory bounds, downstream log privacy, user consent or Stable release safety.

## Source finding

The `obscura-js` console operation records an optional `pending_console_messages: VecDeque<String>` for MCP/buffered page diagnostics. The inherited limit was 1,024 **entries**, without a per-message or total byte budget. A single script-provided console message could be enormous. `Page::suspend_js` additionally appends all buffered messages from the current runtime to `suspended_console_messages` every time a Page is suspended, with no retention cap across repeated switches.

## Implemented controls

- Retain at most **16 KiB of UTF-8 bytes per buffered console message**, including `[level] ` prefix and an explicit ` [truncated]` suffix for oversized text. Slicing respects UTF-8 code point boundaries; ordinary level spelling and message content remain unchanged.
- Retain at most **2 MiB aggregate buffered message bytes and 1,024 entries per live JavaScript runtime**. Enforce both limits on each console append, evicting oldest buffered entries first.
- Apply the same **2 MiB/1,024-entry limit** to `Page::suspended_console_messages` after each suspend; repeated runtime switches cannot retain an unbounded series of historical backlogs.
- Drain/clear APIs continue to return the latest buffered messages and release their retained memory. Only the *optional in-memory text buffer* is altered.

**Importantly**, authorized CDP `Runtime.consoleAPICalled` event arguments are not truncated or dropped by this change. Other `pending_runtime_events`, DOM/V8 allocations, JavaScript strings already allocated before the op call, log sinks and callers retaining drained messages are separate memory/privacy paths.

## Verification

Two Rust unit tests verify oversized Unicode truncation with explicit marker, total byte and entry-count caps, oldest-first retention and newest-message preservation. A Page-side Rust test verifies repeated suspension-retention trimming and drain recovery. The read-only GitHub workflow tests these along with the existing CDP/DOM and owned-loopback PNG/PDF fixtures. Source-level offline tests protect the wiring without asserting global RSS guarantees.

Remaining hostile-client stress, full event metadata overflow handling and all-product retention policies are tracked in [Issue #40](https://github.com/GoreeCloud/headless-browser/issues/40) and [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2). No untrusted third-party sites, public listener, signed binary, container publication or production deployment are involved.
