# Fail-closed Fetch, XHR and document interception

**Status:** Development-source hardening. These limits do not constitute a complete Wardveil egress firewall, GoreeShield privacy approval, or Stable release acceptance.

## Prior risk

The imported interception plumbing used unbounded Tokio request channels, including inside the CDP processor and the public Page API. When the consumer was missing, JS fetch/XHR or document navigation could skip its handler and proceed to the HTTP transport. If an admitted JS request's handler disappeared before resolving, the request could also continue without a decision.

## New safeguards

- Every interception-enabled page and the CDP processor now use a **128-item bounded Tokio MPSC** request channel.
- Each intercepted record, including URL, request/page IDs, method, resource type and header names and values, must carry at most **64 KiB of metadata**. Together, these gates bound retained queued metadata to approximately **8 MiB per channel**, excluding allocation overhead and transient parsing.
- Both the JS operation and document navigation use a shared **nonblocking** admission function. Saturation, closure or oversized metadata fails closed; no direct network request is sent as a fallback.
- If the JS interception handler is dropped after admission but before resolving its one-shot decision, the request is blocked.
- Existing response body limits, URL/SSRF checks, CDP command and reply queues, and WebSocket auth remain independent. Intercepted requests are not trusted because they came from a local page.
- This intentionally changes the pre-Stable Rust sender/receiver API from unbounded to bounded Tokio channels. External consumers must review their compiled integrations and errors before upgrading.

## Verification and limitations

Three Rust unit regressions cover the 129th-queued-request refusal, slot reuse after dequeue, metadata-size rejection and refusal when the consumer is closed. The read-only GitHub job also retains existing compiled JS/CDP checks and owned-loopback browser fixtures. No third-party sites or public CDP endpoints are part of this test.

These bounds do not constrain active JS body sizes, runtime DOM data, renderer allocations, network downloading, one-shot resolver timing, or upstream V8 memory. Further sustained-load and browser-client compatibility testing is required before Stable, as are consent/retention and real-world egress reviews. See [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
