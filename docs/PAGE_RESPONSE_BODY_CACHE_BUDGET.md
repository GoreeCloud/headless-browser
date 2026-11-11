# Aggregate Page Network response-body cache budget

**Status:** Development-source Wardveil cache memory guard. This is not a global RSS or V8 memory limit, and release/client compatibility is pending.

## Previous issue

The Page-owned response cache already had a default maximum of **128 response IDs** and **2 MiB per body**, but could retain up to roughly 256 MiB across 128 independent bodies. `alias_response_body` copied an existing body under the navigation loader ID without applying any cache trim. `suspend_js` moved JS response bodies into the Page cache with a count-only trim and no per-body or aggregate byte check. Those paths could exceed intended memory budgets while preserving `Network.getResponseBody` fidelity.

## New policy

- Add an aggregate **32 MiB default Page cache byte cap** controlled by `OBSCURA_NETWORK_BODY_BUFFER_TOTAL_BYTES`. Count the actual stored binary Vec size of every retained response, including copied aliases.
- Preserve the existing `OBSCURA_NETWORK_BODY_BUFFER_BYTES` default **2 MiB per response** and `OBSCURA_NETWORK_BODY_BUFFER_ENTRIES` default **128 entries**. A new body's accepted size must fit both its per-entry and total cap.
- Reuse oldest-first eviction under **both** count and aggregate-byte limits, with the newest stored response retained preferentially. Replacing an existing request ID updates its position once, preventing stale order keys.
- A new alias has its own copied Vec and consumes bytes; if retaining it exceeds the aggregate cap, evict oldest bodies as needed. This can evict its source body, as allowed by existing cache eviction semantics.
- The JS suspension transfer path uses the same normal body-storage function and budgets instead of writing directly to the map.
- `take_response_body_raw` removes a body and its order entry, transferring ownership to the CDP stream caller; `clear_response_bodies` releases cached copies as before.

**Network event telemetry is not trimmed here.** If a client asks for an older evicted response, `Network.getResponseBody` may no longer find it; that has always been possible under count-based eviction and oversized-body refusal. Document and test that compatibility trade-off rather than silently removing Network events.

## Verification and limitations

Two Rust regressions use inert memory-only responses: aggregate eviction with alias duplication and unique-order handling, plus removal/recovery and cache clear. The readonly GitHub workflow retains owner-only CDP/DOM and PNG/PDF tests.

This cap only accounts for Page-owned raw response-body Vecs; it excludes JavaScript runtime response caches, retained `NetworkEvent` metadata, aliases held by callers, decoded images, in-flight transfers, cache/key allocations, and global browser memory. The new environment variable can be configured, so deployment must enforce a safe bound. Remaining Page event-retention work is tracked in [Issue #40](https://github.com/GoreeCloud/headless-browser/issues/40). No public endpoint, build artifact publication or deployment is involved.
