# Aggregate JavaScript Network response-body cache budget

**Status:** Development-source Wardveil memory hardening; not total process isolation or Stable CDP acceptance.

## Risk

The JavaScript operation layer stores completed Fetch/XHR and module-response strings in `ObscuraState.network_response_bodies` for later `Network.getResponseBody` use. The inherited limits were **128 entries** and **2 MiB per original response body**, with no total byte limit. A base64-encoded body can require approximately 4/3 the bytes of its binary source. Repeated requests could thus retain hundreds of MiB of JS-side strings independently from the Page raw-body cache.

## Policy

- Honor the new `OBSCURA_NETWORK_BODY_BUFFER_TOTAL_BYTES` setting, with a **32 MiB default per JS runtime**. Count the actual UTF-8 byte length of each stored response String, including base64 expansion.
- Preserve the existing per-original-response `OBSCURA_NETWORK_BODY_BUFFER_BYTES` default **2 MiB** and `OBSCURA_NETWORK_BODY_BUFFER_ENTRIES` default **128**.
- Evict oldest cached body Strings until both limits hold; a duplicate request ID occupies one FIFO position, moved to the tail on replacement. An oversized replacement does not leave a stale body addressable by its ID.
- The lazy cached-body supplier is not invoked for completions failing the original-body size gate. A generated body whose encoded/String bytes exceed the aggregate budget is not cached.
- **Always emit the corresponding JS Network completion event**, whether caching succeeds or not. Eviction can make an old `Network.getResponseBody` unavailable, as existing count limits already could; it does not erase the event record.
- Page and JS caches each have their own budget; their defaults are **not one combined process-wide 32 MiB budget**. Other V8/runtime caches, in-flight response buffers and render resources are additional.

## Verification and remaining work

Two focused default-feature Rust tests check aggregate real String bytes, oldest-first eviction, ID replacements, oversized cached-String refusal, lazy body-provider avoidance and preserved JS completion events. The restricted GitHub Actions validation also builds the native CLI and runs owned-loopback CDP/DOM/PNG/PDF fixtures. A lightweight source regression prevents accidental bypass of aggregate admission.

Outstanding: the `js_network_events` Vec currently keeps at most 4096 elements by dropping the oldest without a protocol-visible overflow signal; `Page.network_events` has no aggregate metadata-byte cap. Both require a carefully designed observable overflow/failure contract and hostile-client/client-compatibility tests under [Issue #40](https://github.com/GoreeCloud/headless-browser/issues/40). Do not claim full denial-of-service defense, privacy consent acceptance or signed release approval. No public endpoint, published binary/container or deployment involved.
