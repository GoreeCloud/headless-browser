# CDP outgoing reply and event backpressure

**Status:** Development source hardening; bounded WebSocket reply queue, not full renderer/process memory or external-client security approval.

The per-connection CDP V8 processor can emit responses and events faster than a slow network reader receives them. Historically those messages went into `mpsc::unbounded_channel<String>`, so the incoming queue limits did not protect the outbound side.

## Design and behavior

- The outbound reply channel now retains a maximum of **512 pending messages** and **32 MiB of queued UTF-8 reply/event text per CDP client**. Both are enforced at enqueue time using separate Tokio semaphore permits. This covers regular command responses, CDP events, pending V8 result replies and screencast frames using the shared reply channel.
- A small `CdpReplySender` wrapper preserves normal send/clone semantics across processor and domain helper functions, but reserves message and byte capacity **before** adding a reply to the underlying channel.
- Permits travel with the queued message. The actual WebSocket sender holds the permits while its asynchronous network write is pending; successful completion, cancellation or connection teardown releases both budgets.
- A failed count or byte reservation marks **only this client** overloaded and notifies its writer task. The writer closes the affected socket; producer helpers that ignored `send` failures cannot continue accumulating unbounded events. The overload state remains sticky for all clones.
- Network writes have a **5-second** timeout and WebSocket close attempts have a **2-second** timeout. A client that stops reading must not keep the writer and its capacity reservations indefinitely.
- A single outbound message over 32 MiB will close the client rather than be sent. Legitimate large screenshots, DOM snapshots and high-frequency events require compatibility evaluation; clients are not guaranteed a per-command overload error.
- The existing native `Browser.close` final-acknowledgment path, inbound 256-message/16 MiB pending command limit and the per-worker live connection cap remain distinct.

## Verification

Targeted Rust tests verify message-slot reuse, queued byte releases, cloned sender overload persistence, client isolation and refusal of an oversized individual response. A nonpublishing CI job exercises these tests before existing native CLI/WebSocket/V8/DOM/PNG/PDF and one-slot admission smokes. The full CI build remains required before merge.

## Remaining risks and release gates

The 32 MiB budget counts outbound queued protocol text, not WebSocket compression, kernel buffers, binary copies inside renderer tasks, V8 heaps, DOM caches, HTTP downloads, disk, all concurrent clients, or process RSS. Separate intercepted-request and pending navigation/event queues still need a code audit and bounded sustained-load benchmarks. No public CDP endpoint, untrusted-site test, signing, container distribution or Stable release approval follows from these tests.
