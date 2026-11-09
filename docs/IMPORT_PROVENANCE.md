# GoreeCloud Headless Browser — source import and provenance

## Import identity

- Product name: **GoreeCloud Headless Browser**
- Classification: **Rebranded Import** / attributed derivative, development preview
- Destination: `GoreeCloud/headless-browser` (public GitHub)
- Original destination branch: `main`, commit `accfeb99a27efdc071cb0c8befbb1902f2375bb4` (`README.md` initial commit)
- Official upstream: `h4ckf0r0day/obscura`
- Imported upstream branch: `main`
- Verified upstream HEAD: `59276a3620aed0320879f60b9f049010d568088c` (November 9, 2026)
- Inherited license: Apache-2.0. Preserve `LICENSE`, `NOTICE`, individual source attribution and vendored third-party licenses.
- Upstream source at import: 520 tracked files, zero submodules.

## Transparent import method

The target branch is an unrelated-history **merge** of the existing GoreeCloud `main` and upstream Obscura `main`, not a force push or an overwrite of the target commit history. Upstream commits remain reachable through the merge's second parent. The original upstream top-level README is preserved as `UPSTREAM_README.md`.

## GoreeCloud-specific modifications

1. Product-facing README, notice, security caveats, and this import record.
2. Workspace repository metadata directed to GoreeCloud.
3. `goreecloud-headless-browser` binary added without removing the original `obscura` and `obscura-worker` entry points; The branded executable identifies itself as GoreeCloud Headless Browser while the original `obscura` executable retains its upstream name in help and startup banners.
4. Docker build and entry point target the new binary name, without executing or publishing a container as part of the import.
5. GitHub CODEOWNERS and issue reporting no longer direct GoreeCloud issues to upstream maintainers.
6. Upstream `.github/workflows/ci.yml`, `docker.yml`, and `release.yml` removed from the active tree to prevent unreviewed build, publish, or release actions. Their prior contents remain in imported Git history. A minimal read-only import-verification workflow replaces them.

Core Rust crate names, internal APIs, protocol identifiers, historical documents, and upstream compatibility names remain unchanged unless separately validated.

## Trust and validation scope

Importing source does not imply that code was built, installed, audited exhaustively, or run against untrusted sites. The inherited build scripts include V8 snapshot generation, and the Rust workspace includes vendored dependencies; they are **not** executed merely to validate this import. A deterministic static verification checks product metadata, attribution, source presence, and disabled publishing workflows. A bounded, nonpublishing CI CLI typecheck, SSRF unit tests and standalone CLI binary builds run only after static/provenance gates pass on an isolated hosted runner. The owned-loopback smoke checks both CLI help identities, private-network denial without opt-in, and verbatim raw-byte fetch from a disposable fixture under explicit opt-in. An additional ephemeral loopback-only CDP HTTP smoke verifies ready-file permissions, discovery metadata, request authority/origin refusal, and bearer-token enforcement. The additional masked-WebSocket smoke tests exercise Browser.getVersion / Target.getTargets on local-only servers using both binary identities and verify Origin and token rejection. These are limited local protocol checks, not navigation, rendering, real-world browsing or remote CDP exposure. End-to-end CDP, container, dependency/legal audit, privacy acceptance, complete security review and platform-specific tests remain future release gates.

## Upstream synchronization strategy

```bash
git remote add obscura-upstream https://github.com/h4ckf0r0day/obscura.git
git fetch obscura-upstream main
# Review the new upstream SHA, diffs, notices, scripts, CI and vulnerabilities.
# Create a dedicated integration branch and perform a reviewed merge.
```

Do not use automated blind force pushes or remove upstream authorship. Resolve conflicts deliberately, reapply GoreeCloud branding/security changes and rerun tests before any merge, publication or deployment. No unattended synchronization has been configured.

## Legal and attribution boundary

Apache-2.0 permits modification and redistribution subject to its terms; original copyright statements and third-party notices must remain intact. This import does not claim ownership of original Obscura source, its logo or trademarks, nor upstream endorsement. Review bundled dependency licenses and branding rights before distributing compiled binaries or imagery.
