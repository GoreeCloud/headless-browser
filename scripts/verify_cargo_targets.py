#!/usr/bin/env python3
"""Inspect Cargo target registrations without invoking upstream build scripts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BINS = {
    "goreecloud-headless-browser": "main.rs",
    "obscura": "main.rs",
    "obscura-worker": "worker.rs",
}


def validate_metadata(doc: dict) -> None:
    cli_packages = [p for p in doc.get("packages", []) if p.get("name") == "obscura-cli"]
    if len(cli_packages) != 1:
        raise ValueError("Expected exactly one obscura-cli workspace package")
    cli = cli_packages[0]
    binaries = {
        t["name"]: Path(t["src_path"]).name
        for t in cli.get("targets", [])
        if "bin" in t.get("kind", [])
    }
    missing = {name: src for name, src in EXPECTED_BINS.items() if binaries.get(name) != src}
    if missing:
        raise ValueError(f"Expected binary names and paths missing or changed: {missing}")
    if any(x.get("name") != "obscura-cli" for x in cli_packages):
        raise ValueError("Cargo workspace package metadata is inconsistent")


def main() -> None:
    # `cargo metadata --no-deps` reads manifests; it does not compile Rust
    # source or execute build.rs. --locked prevents resolution lockfile drift.
    completed = subprocess.run(
        ["cargo", "metadata", "--no-deps", "--locked", "--format-version", "1"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    validate_metadata(json.loads(completed.stdout))
    print("PASS: Cargo registers GoreeCloud, Obscura and worker CLI targets")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as err:
        raise SystemExit(f"FAIL: Cargo metadata validation: {err}") from err
