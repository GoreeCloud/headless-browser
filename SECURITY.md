# Security policy

GoreeCloud Headless Browser is an **unreleased development import**. No production safety or full security audit has been established.

For a potentially sensitive vulnerability, avoid disclosing exploit details in a public issue. Use GitHub's private vulnerability reporting for this repository if enabled, or contact the GoreeCloud project maintainer via `admin@goreecloud.com`. Do not send passwords, API keys, browser profiles, or other secrets with a report.

Do not expose CDP or web automation endpoints to untrusted networks. Require independently tested authentication, network isolation, resource limits, least privilege, and privacy controls before any deployment. Upstream Obscura security documentation and fixes should be reviewed and incorporated through a tracked update process.

## Proxy credential handling

CLI startup logs intentionally report only that a proxy is configured, not its URL or credentials. Do not put passwords, bearer tokens or proxy usernames in command-line process arguments when they can be supplied through `OBSCURA_PROXY` or another approved protected secret mechanism. This mitigates CLI log leaks but does not establish that all upstream network traces, inherited diagnostics, crash reports and browser data paths are credential-safe.


## Outbound address classification

The shared `obscura-ssrf` address guard denies internal, link-local, special-use, and legacy IPv6 site-local (`fec0::/10`) addresses by default, including embedded IPv4 forms. These unit checks verify address classification only. They do not replace egress firewall rules, per-transport checks, redirect/DNS rebinding tests, or authentication of CDP clients. `--allow-private-network` and `OBSCURA_ALLOW_PRIVATE_NETWORK` deliberately relax the guard and must not be enabled for untrusted browsing workloads.

## CDP Host authority validation

The HTTP/WebSocket discovery gateway rejects malformed Host authorities containing userinfo, paths, queries or fragments **before** matching the bound IP/port. This narrows misleading host-spoof inputs such as an attacker name followed by an at-sign and the local IP. An isolated Rust unit test and real ephemeral-loopback HTTP Host-header smoke run as part of the nonpublishing CI pipeline. This control does not replace token authentication, Origin protection, transport isolation or remote access policy.

## Loopback CDP control-plane smoke

Nonpublishing CI launches single-worker development binaries bound only to 127.0.0.1 on ephemeral ports. It verifies the atomic ready-file identity/permission contract, DevTools HTTP discovery authority, foreign Host/Origin refusal, unauthenticated discovery under a locally generated bearer token, and successful authorized discovery. It always terminates each server. This test is **not** authorization to expose CDP beyond localhost or to enable file/private-network access, and its HTTP-only checks do not validate WebSocket command handling, user isolation, traffic interception, rate-limits under load or production-grade identity.

## WebSocket CDP protocol smoke

Nonpublishing CI also exercises the actual WebSocket upgrade and two side-effect-free browser metadata methods (Browser.getVersion and Target.getTargets), using a minimal stdlib RFC6455 client with masked outbound frames and bounded response sizes. It verifies refusal of browser Origins and missing/incorrect bearer tokens while the CDP server stays bound to 127.0.0.1. These are narrow protocol checks, not full WebSocket fuzzing, multi-client isolation, production authentication, navigation safety or screenshot/render acceptance.

## CDP duplicate-sensitive-header rejection

The inbound CDP HTTP and WebSocket gateway rejects repeated Host fields (including mixed-case duplicates) instead of choosing one; any Origin field is refused, and multiple Authorization fields are rejected even with a valid bearer. This prevents disagreement between parsers or intermediaries about which control-plane authority or credential is effective. Targeted Rust and actual owned-loopback HTTP checks are run in nonpublishing CI. This does not replace TLS, remote client identity, network segregation or broader request-smuggling assessment.

## CDP fail-closed startup checks

The development CI runner tests four pre-bind failures: an unauthenticated nonloopback address (using nonlocal documentation-only 192.0.2.123, not a wildcard listener), a bearer token shorter than 32 bytes, forwarded nonloopback authority without authentication, and incomplete forwarded authority configuration. These checks must exit promptly with the expected guard message and **must not publish a ready file**. They do not authorize public CDP exposure; a long token is not proof of adequate production authentication, transport encryption, network isolation or credential governance.

## CDP about:blank and local-file guard

A disposable CI WebSocket session checks that Target.createTarget rejects a deliberately nonexistent file:// URL by default, opens and attaches to about:blank, runs only the harmless expression 6 * 7 using Runtime.evaluate, and closes the target without leaving an active target listing. No external navigation, real filesystem contents, user data, or arbitrary site scripts are involved. Passing does not prove comprehensive local-file isolation, untrusted JavaScript sandboxing, cross-origin protections, remote egress controls or production CDP readiness.

## Owned HTTP fixture and private-network opt-in

An inert, fixed HTML document is served solely from a disposable 127.0.0.1 port with no external resources. The CDP browser must **not** fetch it with the default SSRF settings. A separate fresh loopback-only CDP instance is permitted to fetch exactly that local fixture using the explicit --allow-private-network flag; the test checks its DOM title/marker and target cleanup. This narrow opt-in is only a CI test exception, not a GoreeShield or Wardveil approval to enable internal-network browsing, bypass DNS/redirect restrictions, or visit third-party sites.

## Structured CDP command and response filtering

WebSocket shutdown is recognized only when the parsed CDP request method is exactly `Browser.close`, not when arbitrary JSON params contain that text. Internal `__init` connection envelopes are filtered only when they are top-level control records without a CDP response ID; nested user-result fields remain deliverable. Source regressions and real owned-loopback WebSocket/Runtime tests guard against accidental CDP disconnects and swallowed replies. This is a targeted protocol integrity improvement, not a full WebSocket fuzz test or an authorization policy.

## CDP inbound WebSocket memory budget

Each WebSocket connection now limits incoming CDP frame and reassembled message sizes to 16 MiB. This reduces the per-client memory exposure from Tungstenite's default 64 MiB message limit while leaving outbound CDP screenshot/DOM responses unaffected. CI validates the configured Rust budget and sends only an oversized **masked frame header** to an owned-loopback listener, requiring a prompt refusal without sending a large payload, then confirms that a subsequent valid client still works. This is a per-message parser guard, not a total per-client/process memory budget, rate limiter, proof against hostile clients, or production network policy.

## Exact CDP HTTP discovery request-target routing

The local CDP accept loop classifies `/json`, `/json/list`, `/json/version`, and `/json/protocol` from the parsed HTTP request **target**, not by searching arbitrary header text. This prevents WebSocket request headers or lookalike paths from being misinterpreted as discovery traffic. CI validates exact path and optional query behavior, and verifies an owned loopback WebSocket still upgrades and answers CDP commands when an unrelated header contains `/json/version`. Existing Host/Origin/bearer controls remain in force. This is route-integrity hardening, not a complete HTTP parser or request-smuggling assessment.

## Native rendering feature acceptance

Nonpublishing CI also builds the branded CLI with the optional `render` feature and captures only a static, owned HTML fixture on ephemeral loopback. The fixture contains no external fonts/scripts/images; only this test command opts into private-network access. The screenshot validator checks the PNG signature, IHDR checksum, bounded dimensions and terminating chunk; it intentionally does not distribute any image. This is **not** browser rendering pixel-accuracy validation, an untrusted-page sandbox or egress/privacy acceptance, a cross-platform GPU test, an image supply-chain approval, or a release gate completion.

## In-memory CDP raster PDF fixture acceptance

The render-enabled local-only CDP fixture prints a raster PDF from an inert, explicitly owned `127.0.0.1` HTML document; private-network access is opted in only for that disposable runner. The test validates the PDF magic/EOF, an explicit 4×6-inch media box, a raster image, a bounded 6 MiB decoded file and 8 MiB response, and target cleanup without saving or publishing the PDF. It does **not** establish accessible/selectable text, print layout fidelity, supported arbitrary documents, third-party site privacy, or broad browser/CDP compatibility.

## Reliable CDP Browser.close acknowledgment

The server's dedicated WebSocket sender previously risked losing the `Browser.close` success response because it was aborted immediately after the inbound loop ended. A one-shot final-response path now sends the identity-preserving CDP reply, flushes and closes the socket before returning, with a **two-second timeout** to prevent shutdown deadlock. Owned-loopback CI verifies request ID/session ID preservation, acknowledgment-before-close and listener usability after reconnect. This addresses a narrow protocol lifecycle fault; it is not a guarantee of all queued messages, pending tasks or on-disk state during abrupt termination.

## CDP inbound command backpressure

The WebSocket-to-V8 command channel now has a per-client **256-message** capacity and an independent **16 MiB queued UTF-8 byte budget** using Tokio semaphore permits retained by each message until it is processed or dropped. A client exceeding either limit is disconnected rather than growing a queue indefinitely or generating an unbounded error flood. Rust unit tests verify permit release and queue overflow; owned-loopback CDP CI protects expected normal behavior. These limits do **not** constrain outbound events, JS interception queues, V8/DOM memory, bandwidth, active processing or aggregate process RSS, and they require further Wardveil stress testing before any public CDP exposure or release.

## CDP outgoing reply and event backpressure

In addition to the bounded incoming command queue, the per-client outgoing response/event channel now limits retained text to **32 MiB** across at most **512 queued messages**, with separate semaphore reservations held until socket writing completes. On either overload a shared sticky client flag notifies the WebSocket sender to close **only that connection**, rather than buffer unlimited replies or silently drop protocol events. Socket writes time out after five seconds; close attempts are limited to two seconds. Unit regression tests and owned-loopback CDP/V8/PNG/PDF fixtures cover intended behavior. These are queue-level protections, **not** full process/V8/WebSocket/kernel memory accounting, guaranteed interoperability under heavy event streams, a substitute for client authentication, or a production release approval.

## Slow incomplete CDP WebSocket upgrades

After the bounded HTTP request-head peeker forwards a client to the WebSocket I/O thread, the HTTP Upgrade handshake must finish within **five seconds**. Without that deadline, a non-GET malformed or incomplete request prefix could hold a live CDP connection slot while the WebSocket parser waited for the missing header terminator. Owned-loopback CI tests both CLI identities with a deliberately incomplete, small HTTP request; it checks a second client receives HTTP 503 at a one-slot admission limit and confirms the incomplete client times out and the slot becomes available again. The accept-side silent-connection TTL (10 s), 256 parked-socket limit, 4096-byte head bound, Host/Origin/token policy and nonpublishing workflow remain unchanged. This is a narrow handshake-stage denial-of-service safeguard, not comprehensive rate limiting or production network security acceptance.

## Fail-closed JavaScript and document interception

The JS fetch/XHR and document-navigation interception path now uses a **128-record bounded queue** with a **64 KiB metadata ceiling per request** (at most approximately 8 MiB of retained queued metadata, excluding container and allocator overhead). Producers use a nonblocking enqueue: a full, unavailable or oversized interception handler **blocks the request** instead of silently performing a direct network operation. A handler disappearing while awaiting a one-shot resolution also blocks JS fetch rather than bypassing its configured policy. Existing network/SSRF validation remains independent. Rust tests exercise full, closed and oversized queue cases; nonpublishing CI checks the full source integration and owned-loopback CDP/DOM/render smokes. This is not a general network egress firewall, aggregate process RSS limit, consent acceptance, nor proof of browser/Playwright compatibility. The bounded channel changes a development Rust API surface and requires compatibility review before Stable.

## Exact Fetch resolution routing during navigation

The CDP navigation-interception loop now dispatches `Fetch.continueRequest`, `Fetch.fulfillRequest` and `Fetch.failRequest` only when the parsed CDP **method** is one of those commands, not because the text occurs inside a Runtime.evaluate script or another command's parameters. Previously the substring check could consume an unrelated command without deferring it for normal processing, causing client hangs and lost replies. Rust regressions assert the exact positive and negative behaviors, including JSON-escaped method spelling. This corrects a routing bug, not general CDP interoperability, untrusted-page privacy, rate limiting or Stable release acceptance.

## Bounded unresolved CDP Fetch interception decisions

A bounded interception request channel alone does not prevent an unresponsive CDP automation client from accumulating unlimited `Fetch.requestPaused` decisions after its queued requests are consumed. The per-connection paused-request map now permits **128 unresolved decisions**, refuses duplicate live request IDs without overwriting earlier one-shot resolvers and reaps canceled/closed resolvers before admitting replacements. At capacity, new requests fail closed with `Aborted` instead of emitting unresolvable `Fetch.requestPaused` events or using the direct network. This bounds outstanding decision count, **not** V8 process memory, total response body bytes, arbitrary network egress, user consent or remote-client safety.

## Targeted GoreeShield diagnostic log minimization

Browser frame/script/module, stylesheet, tracker, retry, JavaScript fetch and CDP interception diagnostic statements no longer explicitly interpolate full user URLs or opaque interception request IDs at reviewed sites. Cookie-store load/save traces no longer print filesystem locations. Four offline source-level regressions protect these specific diagnostic patterns, while the read-only CI continues its Rust and owned-loopback browser checks. **These changes do not establish that arbitrary error strings, inherited dependencies, browser debug output, networking libraries or every log sink are free of private data.** Production retention, log access, opt-in diagnostics and GoreeShield privacy acceptance remain open; see [docs/LOG_DATA_MINIMIZATION.md](docs/LOG_DATA_MINIMIZATION.md).

## CDP Fetch.enable admission requires live interception consumer

The CDP `Fetch.enable` command now checks for an existing, nonclosed interception receiver **before** setting per-connection or per-page interception-enabled state. A missing or closed consumer yields a CDP error rather than acknowledging a policy that cannot receive paused requests. The sender is installed on the page before enabling the policy. Rust regressions cover missing, closed and live consumer states. A receiver may still disappear later, in which case the separately enforced fail-closed queue and one-shot behavior governs. This does not alter the lower-level public Page API semantics, establish complete remote egress control, or certify production browser privacy.

## Expiring unanswered interception decisions

An interception-enabled JavaScript Fetch/XHR or HTTP document-navigation request now has a **60-second maximum wait for its one-shot Fetch decision** after admission. The shared `obscura-js` helper times out and drops that request's receiver, blocking the request rather than letting it fall through to a direct network fetch. Document navigation reports `net::ERR_TIMED_OUT`; JS fetch returns a blocked result with a fixed reason. Closed handlers fail closed as before. Two Rust tests distinguish deadline expiry, normal completion and closed producers. This guard bounds the wait for a single decision, **not** overall JS/V8 task lifetime, total process memory, all network requests, or the already-queued WebSocket messages. It can abort legitimate debugging/automation workflows that intentionally pause requests for more than 60 seconds, so client compatibility review remains mandatory before Stable.

## Bounded completed renderer resource results

The per-document image/font resource completion channel now retains at most **16 queued results**, aligned with the existing 16 concurrent background fetches. Async producers await an available channel slot instead of retaining an unlimited number of completed resource payloads while a renderer is busy. Navigation, abandonment and document reinitialization create fresh bounded channels, retaining the old-generation response isolation and cancellation behavior. A render-feature Rust unit test verifies refusal of a 17th pending result and slot recovery on dequeue, with existing owned-loopback PNG/PDF fixtures required in CI. **This limits completed queue cardinality, not response body bytes, active fetch buffers, render caches or overall V8/process memory**; individual images can be large and require a separate byte-accounted budget, and prolonged stalled-renderer stress tests remain open.

## Render-only per-response image and font size ceiling

Render-enabled background Image/Font transport requests now use a **16 MiB decoded-body limit per HTTP response**, instead of the inherited 64 MiB maximum for background images. The existing Font limit was already 16 MiB. The change is limited to the background renderer's `ResourceRequest` and does not alter normal HTML navigation, JavaScript Fetch/XHR, scripts or explicit CDP response bodies. Combined with the 16-item completed-response queue, this gives a **256 MiB theoretical queued binary-body ceiling** per active generation (excluding in-flight downloads, renderer caches, duplicate references, headers, V8 memory, allocator overhead and other tasks). Oversized image/font loads fail to supply rendered bytes, which may affect pages using large assets, so compatibility tests are required before Stable. A feature-gated Rust test verifies the precise transport policy; source and owned-loopback render checks remain release prerequisites.
