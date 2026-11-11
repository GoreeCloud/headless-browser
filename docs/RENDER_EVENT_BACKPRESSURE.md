# Bounded pending render-resource Network observations

**Status:** Wardveil development-source resource control; not Stable browser compatibility, privacy consent, or whole-process memory acceptance.

## Source problem

The render completion channel is already a bounded 16-item Tokio MPSC, and each background image/font HTTP body is limited to 16 MiB. The JavaScript runtime nevertheless drained *every* completion and appended its body-bearing response into a separate unbounded `render_resource_events: Vec<RenderResourceEvent>`. A standalone runtime that services render resources without an attached Page draining Network observations could retain arbitrarily many resource bodies over repeated service steps.

## Implemented policy

- At most **8 pending render-resource observation events** per runtime/document generation.
- At most **64 MiB of retained response body bytes** admitted to this event list. The receiver cannot inspect the next response before removing it from the bounded channel, so admission reserves the full **16 MiB maximum background response size per incoming result**, even when it later proves small or unsuccessful.
- If either limit is reached, leave subsequent completions in the pre-existing 16-slot result channel; producer tasks then backpressure by awaiting a channel slot. **No client-visible event is silently dropped or replaced** due to this gate.
- After the Page or standalone client calls `take_render_resource_events()`, subsequent service turns can admit results again in original FIFO order. Page methods that apply results normally drain and report those events immediately.
- Document replacement and resource abandonment already clear pending events, drop stale generation channels, and cancel obsolete tasks. That lifecycle behavior is unchanged.

## Evidence and boundaries

Two feature-gated Rust regressions exercise an inert nine-response fixture: only eight observations may accumulate, the ninth stays queued, draining releases capacity, and all nine retain order; a separate 4×16 MiB body test verifies the conservative 64 MiB gate. Existing source, low-level CDP/DOM, owned-loopback PNG/PDF and generation-fence checks run in read-only GitHub Actions. A source-level Python wiring test guards the admission call.

This **does not cap** Page-level `NetworkEvent` metadata, HTTP body caches, decoded image surfaces, DOM/V8 heap allocations, active downloads, allocation overhead, or multiple browser workers. High-throughput compatibility and adversarial stress remain open in [Issue #40](https://github.com/GoreeCloud/headless-browser/issues/40). There is no public listener, signed release, image publication or deployment.
