# GoreeShield log data minimization — targeted source audit

**Status:** development source controls. These are targeted, nonpublishing log redactions; not complete data-loss prevention, GDPR certification, or production approval.

## Threat model and scope

User-provided page URLs, request IDs and file-system paths can embed credentials, tokens, private account identifiers, internal hostnames and other personal information. Recording them in tracing logs can violate GoreeShield data-minimization expectations even when the same network operations are intentionally permitted. Logging destinations, retention and access controls remain outside this patch.

## Changes

- The CDP interception diagnostic messages retain method and queue-count context without printing full request URLs or opaque request IDs.
- Browser page/frame, script/module, stylesheet, tracker-block and retry diagnostics preserve event/status context but explicitly mask resource URL/path values, including cross-scheme blocks and frame-cap refusals.
- Cookie-load/save diagnostic messages retain the event and safe aggregate cookie count where available while removing the cookie-store file path.
- The JavaScript fetch completion and render-resource diagnostic events no longer attach full request URLs.
- The source-level regression tests in `tests/goreecloud/test_private_diagnostic_logging.py` flag reintroduction of the specific high-risk interpolations; the existing GitHub provenance job runs the entire Python regression suite before compiling any dependencies.

## Non-goals and remaining work

Some externally supplied or upstream-generated exception strings, HTTP libraries, parser/JS error texts and unknown future log statements may still contain URL values or personal information. This audit does **not** claim full log sanitization or specify production retention, access controls or disclosure preferences. Before release, audit all tracing call sites and third-party loggers with canary-token acceptance tests, define opt-in debug logging and retention, isolate log sinks, and enforce GoreeShield consent, minimization and deletion policies.

No public CDP listener, external website, signed package, container image or production deployment is involved. Track remaining privacy/security/legal release gates in [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
