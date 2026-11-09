# CDP Fetch.enable requires an active interception consumer

**Status:** Development-source Wardveil privacy-boundary hardening. This is not a full public-CDP, network-egress, browser-client interoperability or Stable-release acceptance.

## Problem

The CDP handler previously acknowledged `Fetch.enable` and set its enabled flags even if the connection had no interception message sender. When the receiver was missing, it could leave a page configured for an interception policy that could not receive a `Fetch.requestPaused` decision. The existing Page-level interception behavior could then allow a direct network request instead of applying the policy the automation client believed was active.

## Policy and implementation

- Before changing `ctx.fetch_intercept` state or per-page settings, the CDP handler must observe a **present and nonclosed Tokio interception sender**.
- A missing or closed sender returns the CDP error `Fetch interception consumer unavailable`. The previously disabled state and URL patterns remain unchanged on failure; there is no success acknowledgment.
- The handler installs the verified sender on the target page **before** enabling interception for that page.
- A receiver that closes *after* the initial check is still protected by the existing fail-closed enqueue and dropped-one-shot behavior. The admission check alone cannot eliminate all asynchronous races.
- Existing explicit URL-pattern matching, independent SSRF checks and interception request/decision queue caps are unchanged.

## Evidence

Two focused Rust regressions check missing, closed and live sender behavior; the live path verifies the exact URL patterns and enabled state on both context and page. GitHub Actions executes the tests in a read-only, nonpublishing job before existing owned-loopback CDP and DOM/render acceptance checks.

This change does **not** modify lower-level Page API methods, which may be used outside CDP and need a separate contract review. No third-party website, public listener, distributed binary, container rollout or production deployment is involved. Unapproved privacy, security, licensing, memory and release gates remain in [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
