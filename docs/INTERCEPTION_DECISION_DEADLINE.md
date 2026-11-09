# Fail-closed interception decision deadline

**Status:** Development-source Wardveil resource control. Not a substitute for a complete network egress firewall, high-load memory testing, GoreeShield consent review, or Stable-release acceptance.

## Why this matters

The CDP Fetch/XHR/document interception channel and unresolved-decision map now have independent 128-request capacities. But an automation client that receives a `Fetch.requestPaused` event and never answers can still hold a particular JavaScript fetch or document navigation waiting on its one-shot decision indefinitely. Queue length limits do not impose a time limit.

## Safeguard

- A shared `obscura-js::ops::await_interception_resolution` helper enforces a **60-second Tokio deadline** on each one-shot interception decision, starting when the producer awaits its decision.
- The helper is used by both JavaScript fetch/XHR and document-navigation interception. A valid response before the deadline keeps its normal `Continue`, `Fulfill` or `Fail` semantics.
- An unanswered, closed or canceled one-shot decision fails **closed**; it never authorizes direct HTTP access on timeout. JavaScript receives a blocked result and a short fixed error string. Document navigation maps the deadline to `net::ERR_TIMED_OUT` and a closed sender to `net::ERR_ABORTED`.
- A timed-out producer drops its one-shot receiver. The independently bounded paused-request map can reclaim that canceled resolver on admission when full; no unlimited pending decision growth results from this guard.
- Existing per-connection inbound/outbound CDP budgets, intercepted request metadata limit, auth/Origin/Host enforcement and SSRF checks remain separate and unchanged.

## Tests and limitations

Two Rust regression tests verify that unanswered producers expire under a short injected test deadline, normal resolutions are preserved, and disconnected producers fail closed. The read-only GitHub workflow runs the Rust regressions and existing owned-loopback CLI/CDP/DOM/PNG/PDF cases before merges. An offline wiring test ensures both JS and navigation paths invoke the shared helper.

The 60-second decision limit may interrupt legitimate client debugging sessions intentionally pausing a request longer than one minute. It does not guarantee fairness among pages, bound all active V8 tasks, impose a whole-process RSS limit, cancel unrelated requests, or prevent all hostile-network floods. Product/client compatibility, privacy and release-signing audits remain pending in [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
