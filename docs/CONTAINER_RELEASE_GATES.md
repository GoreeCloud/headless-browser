# GoreeCloud Headless Browser — container release gates

**Status: development recipe, not an approved image, deployment or signed release.**

This records a source-level inspection of the imported and modified [Dockerfile](../Dockerfile) on November 9, 2026. The original Obscura authorship and history remain attributed. Third-party dependency and bundled-asset rights still require independent review.

## Source facts, not runtime acceptance

- The build stage uses the mutable **rust:1-slim-bookworm** tag. A stub-only cache-preparation build may ignore failure, but the **final real-source release build must not**.
- The runtime stage uses **gcr.io/distroless/cc-debian12:nonroot**. No later runtime USER override exists in the currently reviewed Dockerfile. Actual image UID, filesystem writes, capabilities and isolation have **not** been tested.
- The entrypoint is the branded GoreeCloud executable; the original Obscura CLI and worker binaries are also copied.
- Port 9222 is exposed. The container CMD binds **0.0.0.0 inside the container**; the native CLI still defaults to loopback. The imported CDP Rust source refuses nonloopback binding unless OBSCURA_CDP_TOKEN has at least 32 bytes. This is verified by native-binary tests, **not** by running Docker.
- Never set OBSCURA_CDP_TOKEN or OBSCURA_ALLOW_PRIVATE_NETWORK as a baked-in Dockerfile ENV or ARG, nor commit secrets to image layers, shell history or build logs.

## Outstanding before any container distribution or deployment

1. Select approved immutable image digests, independently verify builder/runtime provenance and vulnerability advisories, and document regular patch updates.
2. Build a real image in an isolated runner, verify the final build's exit code and digest, the actual runtime nonroot identity, writable storage/temp paths, readiness and shutdown.
3. Restrict host port publication to loopback or a reviewed private proxy (for example **127.0.0.1:9222:9222**, not an unrestricted public interface). Validate bearer authentication, trusted TLS/Identity controls and network policy. Docker environment variables are often inspectable by administrators: a long token alone is not a production secrets policy.
4. Test least privilege, read-only root filesystem compatibility, dropped capabilities, resource quotas, a hardened seccomp/AppArmor-equivalent policy and disabled privileged/broad host mounts. Test default outbound restrictions, redirects, DNS rebinding and cloud metadata access.
5. Complete all vendored/crates.io license evidence, bundled sponsor/image/font rights, asset-matched SBOM, GoreeShield privacy and Wardveil security acceptance.

## Automated review boundary

Run **python3 scripts/verify_container_source_policy.py** to check the current Dockerfile *without executing Docker*. The narrow structural allowlist normalizes case-insensitive Docker instruction keywords, rejects unreviewed parser directives, and pins a SHA-256 of the 26 reviewed noncomment instructions. It rejects unreviewed builder/runtime stage or instruction changes (including extra lowercase FROM, USER and ENTRYPOINT lines), root runtime overrides, unexpected ADD commands, embedded CDP secrets or private-network bypass, unsafe binary/entrypoint drift and a masked final release build. Updating the source digest requires an explicit code and dependency review. A passing check is **not** a container build, image provenance validation, privilege audit, security certification or redistribution approval.

Track the remaining gate in [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
