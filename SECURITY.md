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

Nonpublishing CI launches single-worker development binaries bound only to 127.0.0.1 on ephemeral ports. It verifies the atomic ready-file identity/permission contract, DevTools HTTP discovery authority, foreign Host/Origin refusal, unauthenticated discovery under a locally generated bearer token, and successful authorized discovery. It always terminates each server. This test is **not** authorization to expose CDP beyond localhost or to enable file/private-network access, and does not validate WebSocket command handling, user isolation, traffic interception, rate-limits under load or production-grade identity.

## CDP duplicate-sensitive-header rejection

The inbound CDP HTTP and WebSocket gateway rejects repeated Host fields (including mixed-case duplicates) instead of choosing one; any Origin field is refused, and multiple Authorization fields are rejected even with a valid bearer. This prevents disagreement between parsers or intermediaries about which control-plane authority or credential is effective. Targeted Rust and actual owned-loopback HTTP checks are run in nonpublishing CI. This does not replace TLS, remote client identity, network segregation or broader request-smuggling assessment.
