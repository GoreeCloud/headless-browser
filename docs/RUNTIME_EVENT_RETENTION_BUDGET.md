# Bounded Runtime console/exception observation metadata

**Status:** Wardveil development-source resource guard and GoreeShield privacy-minimized overflow notification, not system-wide RSS or Stable automation compatibility acceptance.

## Previously independent retention

The JavaScript runtime maintains `ObscuraState.pending_runtime_events: VecDeque<RuntimeEvent>`, separately from the bounded optional console text buffer. It accepts `Runtime.consoleAPICalled` argument objects (`serde_json::Value` trees), `Runtime.exceptionThrown` descriptions/stacks and document lifecycle notifications. An inherited **1,024-entry count limit** did not constrain the size of one argument tree or the combined retained payload. A downstream CDP outgoing queue byte limit cannot prevent an earlier JS runtime from retaining large objects.

## Source policy and event semantics

- Set **1,024 event count**, **256 KiB per-event estimated metadata** and **8 MiB aggregate estimated metadata** budgets per JS runtime. Count visible UTF-8 String bytes and JSON node overhead for arguments/exception frames as a conservative retained-object estimate; this is not an exact allocator/RSS accounting method.
- Reject oversized console argument JSON input above 256 KiB before calling `serde_json::from_str`; retain no parsed Runtime console event from that invocation. The separate optional text console buffer already has its own 16 KiB/2 MiB limits and the server log records only level/length, not text.
- Use one insertion/eviction helper for console events, uncaught exceptions and lifecycle events. If an event is too large, count and discard that event. If a new accepted event would exceed count or aggregate budget, release oldest events until it fits. All dropped counts saturate without collecting lost payloads.
- On the next Page Runtime CDP flush, atomically drain retained events and the lost count, resetting the queue's byte budget. Emit **nonstandard** `GoreeCloud.runtimeEventOverflow` with only `{"source":"runtime","droppedEvents":N}` to Runtime- or lifecycle-enabled sessions observing the same Page, before surviving `Runtime.consoleAPICalled`/`Runtime.exceptionThrown` records. No fake Chrome event is generated. Sessions for unrelated targets receive no Runtime extension; Page-only lifecycle subscriptions receive the count-only gap because both event types share the same retained queue.
- Preserve existing `Runtime.consoleAPICalled` argument objects and exception identities/stack details for **accepted** events. Rejecting events under explicit memory pressure is intentionally incompatible with a lossless instrumentation stream; clients ignoring unknown CDP extension methods may see incomplete logs.

## Validation and limitations

Three Rust source tests check old-first 1,024-entry retention, 8 MiB cumulative JSON byte eviction, 256 KiB single-event/large-array/exception refusal and FIFO recovery. A CDP Rust test checks notification payload minimization, same-target session filtering and no notice replay when the count is zero. Read-only GitHub Actions runs these as well as prior native CDP/DOM and owned-loopback PNG/PDF gates.

The legacy standalone `take_pending_runtime_events()` API still returns only surviving events and cannot supply an extension notification; consumers requiring gap counts should use `take_pending_runtime_events_with_overflow()`. The serialized input String and V8 exception object have already been allocated before the queue budget applies; V8/DOM/JS runtime heap growth, parser allocations, interpreter work, CDP output serialization/copies, all other queues and process RSS are unbounded by this policy. Full consent/retention, multiworker stress and Playwright/Puppeteer compatibility remain in [Issue #49](https://github.com/GoreeCloud/headless-browser/issues/49), [Issue #40](https://github.com/GoreeCloud/headless-browser/issues/40) and overarching [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).

No third-party websites, public listeners, signed binaries, images, release workflows or production deployments are used or approved here.
