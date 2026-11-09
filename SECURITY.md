# Security policy

GoreeCloud Headless Browser is an **unreleased development import**. No production safety or full security audit has been established.

For a potentially sensitive vulnerability, avoid disclosing exploit details in a public issue. Use GitHub's private vulnerability reporting for this repository if enabled, or contact the GoreeCloud project maintainer via `admin@goreecloud.com`. Do not send passwords, API keys, browser profiles, or other secrets with a report.

Do not expose CDP or web automation endpoints to untrusted networks. Require independently tested authentication, network isolation, resource limits, least privilege, and privacy controls before any deployment. Upstream Obscura security documentation and fixes should be reviewed and incorporated through a tracked update process.

## Proxy credential handling

CLI startup logs intentionally report only that a proxy is configured, not its URL or credentials. Do not put passwords, bearer tokens or proxy usernames in command-line process arguments when they can be supplied through `OBSCURA_PROXY` or another approved protected secret mechanism. This mitigates CLI log leaks but does not establish that all upstream network traces, inherited diagnostics, crash reports and browser data paths are credential-safe.
