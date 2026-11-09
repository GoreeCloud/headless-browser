#!/usr/bin/env python3
"""Deterministic offline inventory and structural lockfile validation.

This is not a license audit, complete SBOM, dependency code verification, or
security-vulnerability scanner. Never fetch, compile, or execute dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = "registry+https://github.com/rust-lang/crates.io-index"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def local_manifests(root: Path) -> dict[str, dict[str, str]]:
    workspace = tomllib.loads((root / "Cargo.toml").read_text(encoding="utf-8"))
    defaults = workspace["workspace"]["package"]
    paths = sorted((*root.glob("crates/*/Cargo.toml"), *root.glob("vendor/*/Cargo.toml")))
    packages: dict[str, dict[str, str]] = {}
    for path in paths:
        data = tomllib.loads(path.read_text(encoding="utf-8"))["package"]
        name = data["name"]
        require(isinstance(name, str) and name, f"invalid package name at {path}")
        require(name not in packages, f"duplicate local package manifest: {name}")
        version = data.get("version", {})
        if isinstance(version, dict):
            require(version.get("workspace") is True, f"unrecognized workspace version: {name}")
            version = defaults["version"]
        license_spec = data.get("license")
        if isinstance(license_spec, dict):
            require(license_spec.get("workspace") is True, f"unrecognized workspace license: {name}")
            license_spec = defaults.get("license")
        require(isinstance(version, str) and version, f"invalid version: {name}")
        packages[name] = {
            "version": version,
            "manifest": str(path.relative_to(root)),
            "manifest_license_claim": license_spec if isinstance(license_spec, str) else "",
        }
    require(bool(packages), "no workspace/vendor manifests found")
    return packages


def validate_lock(
    lock: dict,
    manifests: dict[str, dict[str, str]],
) -> list[dict[str, str | None]]:
    require(lock.get("version") == 4, "unexpected Cargo.lock format version")
    records = lock.get("package")
    require(isinstance(records, list) and bool(records), "missing Cargo.lock packages")
    identities: set[tuple[str, str, str]] = set()
    result: list[dict[str, str | None]] = []
    encountered_local: set[str] = set()

    for package in records:
        require(isinstance(package, dict), "malformed Cargo.lock package")
        name = package.get("name")
        version = package.get("version")
        source = package.get("source")
        require(
            isinstance(name, str) and bool(name) and isinstance(version, str) and bool(version),
            "malformed Cargo package identity",
        )
        require(source is None or isinstance(source, str), f"invalid source: {name}")
        identity = (name, version, source or "")
        require(identity not in identities, f"duplicate Cargo lock identity: {identity}")
        identities.add(identity)

        if source is None:
            local = manifests.get(name)
            require(local is not None, f"unrecognized local dependency: {name}")
            require(local["version"] == version, f"local version mismatch: {name}")
            encountered_local.add(name)
            row = {
                "name": name,
                "version": version,
                "origin": "workspace_or_vendor",
                "source": None,
                "checksum": None,
                "manifest_license_claim": local["manifest_license_claim"] or None,
            }
        else:
            require(source == REGISTRY, f"unreviewed dependency source: {name} ({source})")
            checksum = package.get("checksum")
            require(
                isinstance(checksum, str) and re.fullmatch(r"[0-9a-f]{64}", checksum) is not None,
                f"missing/invalid registry checksum: {name} {version}",
            )
            row = {
                "name": name,
                "version": version,
                "origin": "crates_io_registry",
                "source": source,
                "checksum": checksum,
                "manifest_license_claim": None,
            }
        result.append(row)

    require(
        encountered_local == set(manifests),
        f"local manifest/lockfile drift: missing={sorted(set(manifests) - encountered_local)}",
    )
    return sorted(result, key=lambda row: (row["name"] or "", row["version"] or "", row["origin"] or ""))


def inventory(root: Path = ROOT) -> dict:
    manifests = local_manifests(root)
    lock = tomllib.loads((root / "Cargo.lock").read_text(encoding="utf-8"))
    records = validate_lock(lock, manifests)
    return {
        "format": "goreecloud-headless-cargo-source-inventory-v1",
        "cargo_lock_format": lock["version"],
        "total_locked_packages": len(records),
        "checksummed_registry_packages": sum(r["origin"] == "crates_io_registry" for r in records),
        "local_workspace_or_vendor_packages": sum(r["origin"] == "workspace_or_vendor" for r in records),
        "dependency_license_audit_complete": False,
        "packages": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit deterministic full lock inventory")
    args = parser.parse_args()
    report = inventory()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            "PASS: Cargo.lock structural source inventory: "
            f"{report['total_locked_packages']} packages, "
            f"{report['checksummed_registry_packages']} registry checksums, "
            f"{report['local_workspace_or_vendor_packages']} local manifests"
        )
        print("NOTICE: no download verification, license clearance or vulnerability scan was performed")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, tomllib.TOMLDecodeError) as error:
        raise SystemExit(f"FAIL: dependency source inventory: {error}") from error
