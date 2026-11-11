# Page Network event metadata retention and count-only overflow

**Status:** Wardveil development-source bounded retention; nonstandard protocol event; not Stable browser compatibility or whole-process memory isolation.

## Risk and source ownership

`Page::network_events: Vec<NetworkEvent>` accumulates pending navigation, fetch/XHR, image and resource observations before multiple CDP flush sites consume them. Earlier improvements bounded image/font result queues, response-body caches and the JavaScript event queue; they did not cap **Page-owned** pending event metadata. Each retained record includes URL, request ID, method, resource type and possibly arbitrary response-header names/values and error text, while a stalled or otherwise late consumer can delay draining it. A count-only JS overflow marker may also be carried by a surviving Page event.

## Implemented memory and protocol policy

- Retain at most **512 Page NetworkEvent records** and **4 MiB of counted UTF-8 metadata String bytes** (request ID, URL, method, resource type, optional error text and both request and response header names/values). These are per-Page pending-event limits. They are **not** an exact Rust heap/RSS bound; container allocations, Arc backing and other subsystems are separate.
- Evict oldest **non-Document** records first to preserve an in-flight Document request's loader-ID identity whenever feasible. A single Document with oversized metadata cannot fit within the budget and can itself be evicted, so this does not guarantee loader identity for adversarial, oversized HTML/HTTP headers.
- Count evicted Page events using a saturating u64. If an evicted Page event also carried a previously recorded **JavaScript** overflow marker, preserve that dropped-JS count separately. No lost URL/request ID/header/body is retained.
- The owning Page and the CDP client are not assumed to support blocking enqueue. Instead, all **five** existing CDP drain sites flush counts alongside surviving metadata: navigation, history traversal, autonomous background resources, pending Runtime navigation, and server-managed navigation.
- The source session and same-target observer sessions receive a **GoreeCloud-specific** `GoreeCloud.networkEventOverflow` notification with `{"source":"page","droppedEvents":N}`. If a JS gap marker was evicted before emission, a separate notice uses `{"source":"javascript","droppedEvents":M}`. Every notice is emitted before surviving Network events, even if there were no survivors.
- The extension is not a normal Chrome Network request, response or failure. It does not forge `Network.requestWillBeSent`, `responseReceived` or `loadingFailed`. Clients ignoring unknown methods **may still miss the event-loss warning**; consumers requiring complete network logs must listen for `GoreeCloud.networkEventOverflow`. Unrelated target sessions do not receive the notice.
- Document replacement accounts for any pending prior-document metadata discarded before the new document starts. Normal draining resets the Page/JS overflow counters so the same loss is not repeatedly reported.

## Verification and remaining risks

Rust regressions cover oldest-first count eviction and recovery, a single oversized retained URL, preservation of previous JS overflow notices, navigation Document survival, one-shot count drain, protocol payload minimization and same-target observer fanout. Read-only GitHub CI runs those with the existing local CDP, DOM, raster PNG and PDF fixtures on a disposable hosted runner.

The public `Page.network_events` Vec remains a low-level internal API that external Rust embedders could mutate directly; the insertion control covers Page's own source producers. The JS event queue also retains its own count cap and separate overflow semantics. This source change has no system-wide memory cap, no bounded V8/DOM or image-decode expansion, and no accepted high-throughput Playwright/Puppeteer or adversarial slow-client assessment. Full source/licensing/privacy and Stable release gates remain in [Issue #40](https://github.com/GoreeCloud/headless-browser/issues/40) and [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).

No untrusted third-party site, public listener, container publication, signed binary or production deployment is involved.
