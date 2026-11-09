# CDP connection admission and recovery acceptance

**Scope:** Nonpublishing, disposable `127.0.0.1` development validation only. Not a production rate limit, complete anti-DoS policy, or security release clearance.

The imported CDP server supports `--max-connections N`, defaulting to 128 live WebSocket clients per worker. A connection consumes a slot while its CDP processor and V8 runtime are active. The server must refuse a connection arriving at the limit with HTTP 503, rather than admitting it and exhausting per-connection resources.

## Automated test

`python3 scripts/verify_cdp_connection_cap_smoke.py` launches a fresh owned-loopback server with `--workers 1 --max-connections 1` independently for both `goreecloud-headless-browser` and the compatibility binary `obscura`. It checks:

- The first native WebSocket upgrades successfully and handles `Browser.getVersion`.
- An additional native WebSocket is refused with **HTTP 503 Service Unavailable** while the first remains live.
- The incumbent WebSocket remains usable after the refused client's attempt.
- After the incumbent disconnects, a replacement is admitted and answers `Browser.getVersion`, with a five-second bounded retry window for asynchronous cleanup.
- No private-network opt-in, external URL, privileged listener, credential, browser download, or release artifact is required.

The offline Python harness also tests `serve` argument construction and rejects non-positive and noninteger limits. These are client-facing admission tests on an owned fixture. They do **not** prove fairness, total memory caps, network rate limits, multiworker aggregate enforcement, leaked V8 state cleanup under panics, or remote-host safety.

**Pending release gates:** verify multiworker admission, worker shutdown/replacement, OS memory pressure, hostile and malformed-client flooding, token/Origin/Host policies, GoreeShield consent and data minimization, Wardveil network security, and complete supply-chain/licensing controls. See [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
