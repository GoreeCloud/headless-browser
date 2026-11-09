#!/usr/bin/env python3
"""Offline exact-source asset provenance; this is NOT license clearance.

Check inherited binary/image files against the pinned upstream Git tree
without executing or fetching third-party code. All checks run locally.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_SHA = "59276a3620aed0320879f60b9f049010d568088c"
EXPECTED_ASSETS = 18
EXPECTED_SPONSOR_GRAPHICS = 16
ALLOWED_EXTENSIONS = {".png", ".svg", ".gif"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def upstream_entries(root: Path) -> dict[str, str]:
    raw = git(root, "ls-tree", "-r", "-z", UPSTREAM_SHA, "--", "assets/")
    entries: dict[str, str] = {}
    for record in raw.split(b"\x00"):
        if not record:
            continue
        try:
            metadata, path_raw = record.split(b"\t", 1)
            mode, kind, oid = metadata.decode("ascii").split(" ")
            name = path_raw.decode("utf-8")
        except (ValueError, UnicodeError) as exc:
            raise ValueError("invalid pinned Git asset tree entry") from exc
        require(mode == "100644" and kind == "blob", f"unexpected asset mode/type: {name}")
        require(name not in entries, f"duplicate upstream asset: {name}")
        require(PurePosixPath(name).parts[0] == "assets", f"asset escapes root: {name}")
        require(PurePosixPath(name).suffix.lower() in ALLOWED_EXTENSIONS, f"unknown asset type: {name}")
        entries[name] = oid
    return entries


def assert_expected_assets(paths: set[str]) -> None:
    require(len(paths) == EXPECTED_ASSETS, "unexpected imported asset count")
    require("assets/banner.png" in paths and "assets/icon.png" in paths, "missing brand graphics")
    sponsor_paths = {name for name in paths if name.startswith("assets/sponsors/")}
    require(len(sponsor_paths) == EXPECTED_SPONSOR_GRAPHICS, "unexpected sponsor graphic count")
    require(paths == sponsor_paths | {"assets/banner.png", "assets/icon.png"}, "unreviewed asset paths")


def verify_asset_tree(root: Path = ROOT) -> list[dict[str, str | int]]:
    upstream = upstream_entries(root)
    assert_expected_assets(set(upstream))
    current_names = {
        path.decode("utf-8")
        for path in git(root, "ls-files", "-z", "--", "assets/").split(b"\x00")
        if path
    }
    require(current_names == set(upstream), "tracked assets differ from exact pinned upstream set")
    # In a repository checkout, a new untracked image must also be noticed.
    extra = [
        path for path in git(root, "ls-files", "-z", "--others", "--exclude-standard", "--", "assets/").split(b"\x00")
        if path
    ]
    require(not extra, "untracked assets require explicit rights and provenance review")

    records: list[dict[str, str | int]] = []
    for name in sorted(current_names):
        path = root / name
        require(path.is_file() and not path.is_symlink(), f"asset missing or symlinked: {name}")
        bytes_current = path.read_bytes()
        bytes_original = git(root, "show", f"{UPSTREAM_SHA}:{name}")
        require(bytes_current == bytes_original, f"imported asset was changed: {name}")
        require(bytes_current, f"zero-byte imported asset: {name}")
        records.append({
            "path": name,
            "category": "inherited_sponsor_graphic" if name.startswith("assets/sponsors/") else "inherited_obscura_brand_graphic",
            "bytes": len(bytes_current),
            "sha256": hashlib.sha256(bytes_current).hexdigest(),
            "upstream_git_blob_oid": upstream[name],
            "redistribution_rights_verified": "no",
            "trademark_use_verified": "no",
        })
    return records


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit deterministic asset ledger")
    args = parser.parse_args()
    records = verify_asset_tree()
    if args.json:
        print(json.dumps({
            "format": "goreecloud-upstream-asset-provenance-v1",
            "original_obscura_sha": UPSTREAM_SHA,
            "rights_clearance_complete": False,
            "assets": records,
        }, indent=2, sort_keys=True))
    else:
        print(
            f"PASS: {len(records)} bit-for-bit upstream assets "
            f"({EXPECTED_SPONSOR_GRAPHICS} sponsor and 2 original brand graphics)"
        )
        print("NOTICE: origin integrity does not establish branding/trademark or redistribution rights")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, UnicodeError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"FAIL: imported asset source check: {error}") from error
