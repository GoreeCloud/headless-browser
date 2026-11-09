# Render-only image/font transport response size budget

**Status:** Development-source Wardveil memory hardening; not whole-process RSS isolation or Stable-release approval.

## Risk

The render-enabled browser now has a bounded **16-completion queue**, but inherited image transport requests can still read up to **64 MiB decoded body per image**. Sixteen completed images could retain up to approximately **1 GiB** of image bodies in the queue alone, before counting 16 concurrent downloads, renderer caches, header allocations and V8 memory. This is a worst-case size-bound calculation, not measured process RSS.

## Policy

- The background render-resource loader creates its `ResourceRequest` using an explicit `MAX_RENDER_BACKGROUND_RESPONSE_BYTES = 16 * 1024 * 1024` ceiling, enforced by the existing HTTP transport's response cap.
- The normal inherited image request maximum was 64 MiB; it is now 16 MiB **only for the renderer's asynchronous Image/Font fetches**. Font requests were already limited to 16 MiB.
- Existing request mode, credentials, initiator/referrer, CORS profile overrides, SSRF checks and callbacks are preserved. Ordinary page navigation, scripts, Fetch/XHR and explicit CDP requests are not changed by this cap.
- A response exceeding the cap is treated as a failed resource load, with normal pending-result cleanup. The renderer may omit an oversized image or font; this compatibility cost must be evaluated before Stable.
- Combined with the 16-item completed-response queue this limits queued decoded image/font body bytes to approximately **256 MiB per generation**. In-flight requests (up to 16), resource caches and event buffers are additional and are **not** included in that figure.

## Verification and next priorities

A feature-gated Rust regression verifies Image/Font request caps and unchanged normal Script request semantics. The protected GitHub workflow runs this test alongside source-integrity, CDP, DOM and owned-loopback PNG/PDF checks. Source-level offline verification protects the exact bounded background request construction.

Further needed: an aggregate body-byte budget across active and queued render loads, cache/event retention accounting, representative large-image font compatibility, V8/DOM memory limits, process load testing, privacy/consent and supply-chain/legal acceptance. No third-party websites, public listener, signed release, container publication or deployment performed. Track [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
