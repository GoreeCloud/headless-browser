# CDP incomplete WebSocket upgrade deadline

**Status:** Owned-loopback development safety check, not public-network exposure approval or a stable release.

An accepted TCP client must send a full HTTP request head to use the native Chrome DevTools Protocol WebSocket. The dedicated CDP accept thread already peeks at request headers with a 4 KiB size limit, parks at most 256 clients waiting for a complete `GET` head and retires silent connections after 10 seconds. However, a **non-GET or malformed prefix** is forwarded early to Tungstenite to reject it. If a peer sends that prefix plus an authorized `Host` but never finishes the HTTP Upgrade headers, Tungstenite can wait indefinitely, consuming an active connection slot and I/O thread.

## Enforcement

- Wrap `tokio_tungstenite::accept_async_with_config` in a **5-second Tokio deadline**, without relaxing the existing Host/Origin/token and WebSocket frame/message limits. Timeout closes the failed client as the connection task returns; normal WebSocket handshakes are unchanged.
- Keep the separate 10-second accept-side silent TTL, 256 parked-client cap and 4096-byte peek buffer. A request already forwarded to Tungstenite must not depend on the silent parking deadline.
- The targeted Rust test checks the five-second interval and its relationship to the accept-side deadline.
- A nonpublishing integration test starts `--workers 1 --max-connections 1` on ephemeral 127.0.0.1, sends only an incomplete **non-GET** request with the correct local Host header, verifies HTTP 503 for a competing client, verifies the slow client closes within the bounded interval, then checks slot release and successful `Browser.getVersion` on a fresh client. It exercises both GoreeCloud and legacy CLI identities.
- Offline Python regression tests ensure that the synthetic request cannot embed external hosts or arbitrary port strings, and that its terminator is intentionally absent.

## Limits

This is a handshake-stage resource safeguard, not a full HTTP request-smuggling audit, rate limiter, fairness policy, hostile-flood acceptance, total process memory cap, reverse-proxy security contract or privacy/consent approval. The outbound CDP response queue, renderer memory, admission limits, network egress and complete license/SBOM rights review must be accepted separately. See [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
