# Fail-closed interception for direct Page and JavaScript clients

**Status:** Development-source Wardveil/GoreeShield boundary hardening. Not a complete egress firewall or Stable release acceptance.

## Previous gap

The CDP domain now refuses `Fetch.enable` without a live consumer. However, a program using the lower-level `Page::enable_intercept` or JS runtime interception setter can independently set interception-enabled state without installing a matching `InterceptedRequest` receiver. For a URL matching an enabled interception pattern, Page document navigation previously returned `Ok(None)` and JavaScript `fetch()`/XHR returned `None` for its sender, allowing a direct HTTP operation.

## Behavior

- **Page document navigation:** if interception is enabled, its URL matches, and no sender is installed, return a blocked `NetworkError` rather than delegating to HTTP.
- **JavaScript Fetch/XHR:** use a shared sender-selection helper. Matching URLs without a sender return a blocked response, not direct HTTP. Closed senders remain subject to existing nonblocking, fail-closed enqueue rejection.
- **Nonmatching URLs:** keep their original transport behavior, including an enabled pattern that matches a different URL. URL patterns are selection filters, not global blocklists.
- **Already configured CDP clients:** unchanged except for the stricter invariant that missing interception handlers cannot silently bypass interception. CDP admission itself is separately validated.

## Verification and limitations

Targeted Rust tests cover missing and installed JavaScript senders, nonmatching URL patterns and direct Page navigation refusal. The existing owned-loopback parser-script fixture verifies that a nonmatching pattern still permits normal parser scripts. A source-level Python regression guards the exact fail-closed wiring. The nonpublishing GitHub workflow compiles and runs the Rust tests alongside existing CDP/DOM/render/PNG/PDF smokes.

This is source policy, not proof of total network isolation, third-party compatibility, consent implementation or a production service. No third-party websites, public listeners, signed binaries or deployments involved. See [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
