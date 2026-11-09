# GoreeCloud Headless Browser

**Rebranded Import** — a GoreeCloud-maintained, attributed derivative of [Obscura](https://github.com/h4ckf0r0day/obscura), a Rust headless browser engine for web automation and AI agents.

> **Status: development source import.** This repository is not a verified stable release, a production deployment, or a security certification. Compatibility with any specific site, browser client, or operating system requires independent testing.

## Features inherited from Obscura

- JavaScript execution and browser automation through the Chrome DevTools Protocol (CDP).
- Puppeteer and Playwright integration paths, scraping, and page interaction.
- Optional native rendering for screenshots and PDFs.
- Local CLI and server modes, with upstream documentation retained.

These describe upstream capabilities, **not independently verified GoreeCloud functionality**.

## Build and use

The current Rust workspace keeps the original `obscura-*` crate names and APIs to preserve dependency and protocol compatibility. A GoreeCloud-branded CLI entry point is added alongside the existing `obscura` command.

```bash
cargo build -p obscura-cli --bin goreecloud-headless-browser --features render
./target/debug/goreecloud-headless-browser --help
```

The original `obscura` and `obscura-worker` binaries are retained. Both `obscura --help` and `goreecloud-headless-browser --help` retain their appropriate command identity. Building requires Rust and the inherited Obscura toolchain/dependencies; inspect [upstream build instructions](docs/Build-from-source.md) before installing or executing any dependencies. **No build or runtime compatibility is asserted by this import alone.**

## Privacy and security

Treat page content, downloads, browser automation scripts, and remote CDP clients as untrusted. Keep CDP listening on loopback, require suitable authentication for any broader access, enforce network/SSRF restrictions, avoid running the browser as root, and apply GoreeShield privacy and Wardveil security controls before deployment. The upstream software's defaults and safeguards require independent validation for GoreeCloud use.

## Provenance and maintenance

- **Official upstream:** [h4ckf0r0day/obscura](https://github.com/h4ckf0r0day/obscura)
- **Imported upstream branch:** `main`, commit [`59276a3620aed0320879f60b9f049010d568088c`](https://github.com/h4ckf0r0day/obscura/commit/59276a3620aed0320879f60b9f049010d568088c), checked November 9, 2026
- **Import method:** unrelated-history Git merge, preserving upstream commit ancestry and the preexisting GoreeCloud repository history
- **License:** [Apache License 2.0](LICENSE); original authorship, third-party vendor licenses, and [attribution](NOTICE) are retained
- **Original upstream README:** [UPSTREAM_README.md](UPSTREAM_README.md)
- **Integration record:** [docs/IMPORT_PROVENANCE.md](docs/IMPORT_PROVENANCE.md)
- **Upstream feature documentation:** [docs/README.md](docs/README.md)

GoreeCloud Headless Browser is independently maintained. It is **not an official Obscura distribution** and has no implied affiliation or endorsement. The original Obscura project name remains in technical code, inherited APIs, and historical attribution where appropriate.

## Contribution and updates

Changes should enter through reviewed branches/PRs. Upstream changes must be fetched and assessed for licensing, security, tests, build compatibility, and potential conflicts before merging. The upstream Docker-publishing, release, and full-build workflows were deliberately removed from the active import tree; only a read-only, static import validation workflow remains until appropriately reviewed and restored.

### Source-validation scope

The read-only GitHub Actions workflow checks preserved upstream history, licensing attribution and workflows; inspects Cargo binary registration without executing build scripts; tests the isolated CLI identity module; and, only after those checks pass, runs the inherited SSRF unit tests and a bounded Rust CLI typecheck on a disposable hosted runner. The typecheck may execute inherited dependency/build scripts **only inside that CI runner**. This is not a release build, end-to-end CDP test, browser runtime acceptance, complete code/security audit, or deployment.
