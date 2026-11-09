# Bounded pending CDP Fetch request decisions

**Status:** Development-source Wardveil resource hardening. Not complete CDP compatibility, hostile-client resistance, privacy approval or Stable release clearance.

## Problem

The JS/HTTP interception request channel now holds at most 128 unconsumed requests, but each consumed request can be moved into the CDP processor's `HashMap<String, PausedIntercept>` while waiting indefinitely for a remote automation client's `Fetch.continueRequest`, `Fetch.fulfillRequest` or `Fetch.failRequest`. Without a separate bound, sustained traffic could grow unresolved one-shot sender state even though the request queue itself was bounded.

## Policy

- Each CDP processor admits at most **128 simultaneously unresolved `Fetch.requestPaused` decisions**.
- If a request arrives at the limit, the server returns `InterceptResolution::Fail { reason: "Aborted" }` directly to its one-shot resolver and does **not** advertise an unresolvable paused event.
- An incoming request with an already live request ID is rejected rather than overwriting the earlier resolver; valid first requests continue unaffected.
- If a request's consumer was canceled and its one-shot is already closed, stale entries are reaped during admission to recover a slot before refusing a new request.
- Existing network/SSRF restrictions, the 128 queued interception records with a 64 KiB per-record metadata limit, CDP 256-command/16 MiB inbound budget and 512-event/32 MiB outbound budget remain separate guards.

## Verification

The targeted Rust regression constructs 128 live paused resolvers, checks refusal of overflow and duplicate IDs without emitting misleading CDP events, then closes one resolver and verifies the replacement is accepted and emits the expected `Network.requestWillBeSent` and `Fetch.requestPaused` events. The read-only GitHub workflow executes the regression alongside owned-loopback CLI, CDP and render checks.

The cap controls only the **number of unresolved interception decisions**. It does not bound network response bodies, per-page V8 allocations, all copies of request metadata, operating-system memory, total traffic rates or all concurrent processes. It can abort legitimate client workloads with more than 128 unresolved requests; evaluate representative Puppeteer/Playwright sessions before Stable. Issue tracker: [#2](https://github.com/GoreeCloud/headless-browser/issues/2).
