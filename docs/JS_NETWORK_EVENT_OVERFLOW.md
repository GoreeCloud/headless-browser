# Observable JavaScript Network event overflow (CDP extension)

**Status:** GoreeCloud-specific development-source Wardveil/GoreeShield observability; not a Chrome-standard CDP method or Stable compatibility approval.

## Existing behavior

The runtime buffers at most **4,096 JavaScript network observations** from fetch/XHR/dynamic-module completions. When the JavaScript event consumer is stalled, additional events evict the oldest observations from the bounded Vec. Previously, the owning Page could not distinguish a complete record of requests from a truncated one, so CDP clients might silently miss network activity.

## Behavior

- Keep the hard 4,096-event cap rather than making the queue unbounded. Every oldest-first eviction increments a saturating **count-only** counter; discarded URLs, headers, request identifiers and bodies are not saved for later diagnostics.
- The Page drains surviving events and the lost-observation count **atomically** from the runtime. The count resets at that boundary, so subsequent normal drains do not repeat an old warning.
- The Page attaches the count only to the *first surviving* JavaScript event. The CDP runtime and post-navigation network emitters issue a single custom event **before** that surviving request:
```json
{
  "method": "GoreeCloud.networkEventOverflow",
  "params": {"source": "javascript", "droppedEvents": 3},
  "sessionId": "<active session identifier>"
}
```
  The sessionId shown is a schematic field, not a fixed value. The actual notice is scoped to the owning target's active session and the other sessions observing that same target, not unrelated pages.
- The notice is a **GoreeCloud CDP extension**, not a standard Chrome Network event. Chrome-only clients may ignore it; interested tooling should listen to `GoreeCloud.networkEventOverflow` and treat the network log as **incomplete** when `droppedEvents > 0`.
- No normal `Network.loadingFailed` or synthetic success is generated for discarded historical observations. The remaining genuine Network events still emit in their existing order.

## Verification

A Rust runtime test exceeds the 4,096-event queue and verifies retained FIFO, lost-count tracking and the absence of retained discarded metadata. Two CDP Rust tests verify the count-only extension precedes the first surviving event in both runtime and post-navigation flows, fans out to same-target observers, and does not leak into unrelated target sessions. Two Python source-wiring tests protect the counter, atomic drain, count-only payload and event fanout. Nonpublishing hosted CI also exercises native CDP/owned-loopback DOM and PNG/PDF smokes.

## Boundaries and follow-ups

This is **not** a lossless queue, protocol-level backpressure, or a global process-level memory cap. The Page's separate pending `network_events: Vec<NetworkEvent>` metadata is now bounded to 512 entries and 4 MiB of counted text, with an explicit `source=page` overflow notice; see [PAGE_NETWORK_EVENT_BUDGET.md](PAGE_NETWORK_EVENT_BUDGET.md). This is observable event loss, **not** a lossless backpressure policy. Under CDP outgoing queue overload, a connection may already be disconnected before it can receive the notice. Standalone runtime clients using the legacy event-drain API do not receive CDP extensions. Browser-client compatibility, hostile-client endurance testing, source/asset licensing, consent/retention policy, V8/DOM memory and Stable/production release remain unaccepted in [Issue #40](https://github.com/GoreeCloud/headless-browser/issues/40) and [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
