#!/usr/bin/env python3
"""Offline static checks for GoreeCloud's attributed Obscura import (stdlib only)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {detail}")


def main() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    original = (ROOT / "UPSTREAM_README.md").read_text(encoding="utf-8")
    manifest = (ROOT / "Cargo.toml").read_text(encoding="utf-8")
    cli = (ROOT / "crates/obscura-cli/Cargo.toml").read_text(encoding="utf-8")
    main_rs = (ROOT / "crates/obscura-cli/src/main.rs").read_text(encoding="utf-8")
    docker = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

    require(readme.startswith("# GoreeCloud Headless Browser"), "product title")
    require("Rebranded Import" in readme, "import classification")
    require("# Obscura" in original or "<h2 align=\"center\">Obscura</h2>" in original, "original README preserved")
    require("h4ckf0r0day/obscura" in notice, "upstream attribution")
    require("59276a3620aed0320879f60b9f049010d568088c" in notice, "upstream SHA recorded")
    require("Version 2.0, January 2004" in license_text, "Apache-2.0 license preserved")
    require('repository = "https://github.com/GoreeCloud/headless-browser"' in manifest, "GoreeCloud repository metadata")
    require('name = "goreecloud-headless-browser"' in cli and 'name = "obscura"' in cli, "branded and compatibility CLI bins")
    require('name = "goreecloud-headless-browser"' in main_rs, "branded CLI help")
    require('ENTRYPOINT ["/goreecloud-headless-browser"]' in docker, "branded Docker entry point")
    for filename in ("ci.yml", "docker.yml", "release.yml"):
        require(not (ROOT / ".github/workflows" / filename).exists(), f"upstream {filename} disabled")
    require((ROOT / "vendor/taffy/LICENSE").is_file(), "taffy vendor license")
    require((ROOT / "vendor/wreq-util/LICENSE").is_file(), "wreq-util vendor license")
    print("PASS: attributed GoreeCloud import, compatibility metadata and publish-workflow gates")


if __name__ == "__main__":
    main()
