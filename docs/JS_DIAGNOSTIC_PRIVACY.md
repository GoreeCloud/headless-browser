# GoreeShield: JavaScript console and evaluation diagnostic minimization

**Status:** Targeted source-level privacy hardening, not full log-sink or retention certification.

## Exposure

JavaScript runtime console arguments and evaluation expressions are user/page-controlled text. They may contain authentication values, private user content, URL tokens or application data. The imported browser wrote raw `console.log`, `console.warn`, and `console.error` message Strings into server tracing. On failed evaluation, it also logged up to 80 bytes of the submitted JS expression (plus exception text), and CDP evaluation/callFunctionOn errors were logged verbatim.

## Policy

- Server-side `obscura::console` tracing now records only severity and byte length. It never interpolates the page message String into log text.
- The Page `evaluate` and `evaluate_with_timeout` failure handlers record fixed short diagnostics instead of raw caller expression/exception Strings. The obsolete caller-text truncation helper and its narrow test are removed; truncating to 80 bytes is not a privacy control.
- `evaluate_for_cdp` and `callFunctionOn` error logs use fixed, redacted descriptions. Their API fallback responses are unchanged.
- **CDP console events and the in-memory console buffer are unchanged**; they retain original messages for enabled consumers. This avoids silently altering the browser-client protocol, but it means clients and storage consumers still need explicit privacy/consent and retention controls.

## Verification and remaining risk

The offline source regression verifies that the relevant tracing sites no longer embed console/JS text and that the in-memory/CDP console code still receives its original payload. The read-only GitHub workflow compiles the dependent Rust crates and runs the native owned-loopback browser tests. Other JavaScript parser errors, exception stacks, upstream library errors and arbitrary third-party tracing may still include private strings. Log sink access, retention, purge and user consent are separate GoreeShield release gates.

No third-party website is contacted or public listener, binary, image, Stable release or production deployment created. See [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
