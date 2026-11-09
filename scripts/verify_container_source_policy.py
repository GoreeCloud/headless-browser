#!/usr/bin/env python3
"""Narrow offline Dockerfile source policy for a nonpublishing import.

This is NOT a Docker build, container privilege/isolation test, provenance
attestation, production configuration audit, or third-party base-image scan.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def instructions(dockerfile: str) -> list[str]:
    """Join Dockerfile backslash continuations, ignoring full comment lines."""
    rows: list[str] = []
    pending = ""
    for source in dockerfile.splitlines():
        line = source.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\"):
            pending += line[:-1].rstrip() + " "
        else:
            rows.append((pending + line).strip())
            pending = ""
    if pending:
        raise ValueError("unfinished Dockerfile continuation")
    return rows


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def verify_dockerfile(text: str, cdp_source: str) -> None:
    rows = instructions(text)
    froms = [(index, row) for index, row in enumerate(rows) if row.startswith("FROM ")]
    require(len(froms) == 2, "expected exactly reviewed build and runtime stages")
    require(froms[0][1] == "FROM rust:1-slim-bookworm AS builder", "unreviewed builder base image")
    require(
        froms[1][1] == "FROM gcr.io/distroless/cc-debian12:nonroot",
        "runtime must use reviewed nonroot distroless base",
    )
    runtime = rows[froms[1][0] + 1:]
    require(not any(row.startswith("USER ") for row in runtime), "runtime USER overrides nonroot base")
    require(not any(row.startswith("RUN ") for row in runtime), "unexpected runtime shell command")
    require(not any(row.startswith("ADD ") for row in rows), "unreviewed Docker ADD directive")

    for row in rows:
        if row.startswith(("ENV ", "ARG ")):
            require(
                not any(name in row for name in ("OBSCURA_CDP_TOKEN", "OBSCURA_ALLOW_PRIVATE_NETWORK")),
                "secret or private-network opt-in embedded at Docker build time",
            )
        require("--privileged" not in row, "privileged container flag in Docker source")
        require("curl " not in row or "| sh" not in row, "unreviewed pipe-to-shell download")

    require("EXPOSE 9222" in runtime, "CDP container port changed without review")
    require(
        'ENTRYPOINT ["/goreecloud-headless-browser"]' in runtime,
        "unreviewed container executable entrypoint",
    )
    require(
        'CMD ["serve", "--port", "9222", "--host", "0.0.0.0"]' in runtime,
        "review the explicit container bind and authentication policy",
    )
    for binary in ("obscura", "goreecloud-headless-browser", "obscura-worker"):
        require(
            f"COPY --from=builder /build/target/release/{binary} /{binary}" in runtime,
            f"missing container binary: {binary}",
        )

    # The stub-only cargo prefetch can ignore failure, but the actual source
    # build MUST propagate errors; hiding a release build failure is unsafe.
    full_build = text.split("# Copy real sources and build", 1)
    require(len(full_build) == 2, "real-source build section is missing")
    real_build = full_build[1].split("# ---", 1)[0]
    require(
        "cargo build --release" in real_build and "|| true" not in real_build,
        "actual source release build must be unmasked",
    )
    require(
        "refusing to expose CDP without authentication" in cdp_source,
        "container wildcard bind requires tested CDP authentication refusal",
    )


def main() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    cdp_source = (ROOT / "crates/obscura-cdp/src/server.rs").read_text(encoding="utf-8")
    verify_dockerfile(dockerfile, cdp_source)
    print("PASS: reviewed nonroot Docker source, bounded bind, no embedded token and unmasked real build")
    print("NOTICE: mutable base tags, runtime isolation, SBOM and asset licensing remain unapproved")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        raise SystemExit(f"FAIL: Docker source policy: {error}") from error
