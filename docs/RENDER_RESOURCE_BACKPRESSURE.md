# Bounded image/font render-resource completion queue

**Status:** Development-source Wardveil resource backpressure. Not total process memory accounting, external browser-client acceptance or Stable release approval.

## Existing risk

The renderer already limits concurrent background resource requests to **16**. However, each completed image/font response was sent through an **unbounded Tokio MPSC** queue carrying the full decoded response bytes. When the V8/page renderer stops draining the queue, continued successful fetches could retain an ever-growing number of completed images/fonts despite bounded fetch concurrency.

## New behavior

- All render-resource completion paths now use a **16-slot Tokio bounded MPSC channel**, matching the current `RENDER_RESOURCE_CONCURRENCY` setting.
- The background loader is asynchronous. It awaits `sender.send(load)` when the queue reaches capacity, rather than accumulating arbitrary completed responses or dropping ordinary results under load.
- The initial state and all three channel recreation sites (document reinitialization, explicit abandonment and detached DOM) consistently create bounded channels. Once the document generation retires, its receiver is dropped and late senders exit without applying stale results.
- Existing render-resource consumer logic still drains all currently completed entries on servicing, and the underlying network transport's per-resource response-size limits remain independent.

## Verification and limits

A render-feature Rust regression fills all 16 channel slots, verifies refusal of a 17th result with `TrySendError::Full`, drains one slot and successfully admits a replacement. A Python wiring regression checks that the producer uses `send(...).await`, and every channel reset uses the same capacity. The read-only CI job compiles the render-enabled crate, runs these tests and exercises owned-loopback PNG and PDF fixtures.

**Important:** this caps the **number of completed responses queued**, not their total bytes. An individual image can be up to the network response's existing 64 MiB limit, while 16 transport operations may be in flight; copies, render caches, layout/V8 allocations and multiple clients are not included. A subsequent byte-accounted budget and sustained-load test are needed before public CDP exposure or Stable release. No unknown site, packaged image/binary, release or deployment was introduced. See [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
