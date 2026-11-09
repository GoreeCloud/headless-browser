# CDP inbound command backpressure — source design and acceptance

**Development status:** bounded per-connection *incoming command* queue. This is a targeted Wardveil resource safety guard, not a complete remote-CDP security review, traffic rate limit, process RSS cap, or Stable release approval.

## Before this change

Although the CDP WebSocket parser capped individual inbound messages at 16 MiB and the accept loop bounded live sessions, the channel forwarding commands from each WebSocket I/O task to its V8 processor was unbounded. A processor held busy or stalled could accumulate command strings without an application-level queue budget.

## New safeguards

- A Tokio `mpsc::channel` holds **at most 256 pending commands** per live connection, including an initialization envelope. This count bounds the number of queued items even when their bodies are small or empty.
- A separate per-connection `Semaphore` reserves **one permit per queued UTF-8 byte**, with a total budget of **16 MiB**. A permit travels with the command until it is processed, deferred or canceled; dropping the message automatically returns its permits.
- Admission is nonblocking. If either the count or byte budget would be exceeded, the server **closes that client's WebSocket** instead of blocking the I/O runtime, accumulating unlimited work or buffering unlimited error replies. Existing clients and the listener remain unaffected by the overload decision.
- The established `Browser.close` acknowledgment path and read-only CDP discovery flow remain independent of this command queue. Normal WebSocket responses still have their existing transport semantics.

## Evidence and release limitations

Unit tests assert that byte permits remain unavailable while a request owns them and become reusable when the request is dropped, including near-limit and over-limit cases. A separate test verifies that the bounded message channel refuses its 257th queued item. GitHub Actions compiles the full Rust test crate and runs both target tests, followed by existing native-CDP, owned-page, render, PDF and connection-capacity fixture checks.

The incoming *response/event* channel and JavaScript interception-request channel still require separate backpressure review. Queued-message bytes are not the entire process's memory footprint: active V8 isolates, decompression, parser copies, DOM, screenshots/PDFs and runtime allocations are not counted. The limits may reject legitimately large bursts of CDP requests; compatibility testing must include representative Playwright/Puppeteer workloads before a Stable claim.

No untrusted website browsing, public listener, package publication, container rollout or deployment is authorized by this change. Remaining release gates are tracked in [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
