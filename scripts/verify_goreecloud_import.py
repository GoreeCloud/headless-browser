#!/usr/bin/env python3
"""Offline source-import, provenance and no-publish checks (Python 3.11+).

Do not import or execute inherited Obscura code to perform these checks.
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_SHA = "59276a3620aed0320879f60b9f049010d568088c"
INITIAL_SHA = "accfeb99a27efdc071cb0c8befbb1902f2375bb4"
GOREECLOUD_REPOSITORY = "https://github.com/GoreeCloud/headless-browser"
VALIDATION_WORKFLOW = ".github/workflows/import-validation.yml"
CHECKOUT_PIN = "d23441a48e516b6c34aea4fa41551a30e30af803"


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(detail)


def git(root: Path, *args: str) -> bytes:
    """Read local Git objects only; never fetch or run project build hooks."""
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def verify_provenance(root: Path) -> None:
    for commit in (INITIAL_SHA, UPSTREAM_SHA):
        try:
            git(root, "merge-base", "--is-ancestor", commit, "HEAD")
        except (OSError, subprocess.CalledProcessError) as error:
            raise ValueError(f"missing imported ancestor {commit}") from error

    for current_file, original_file in (
        ("UPSTREAM_README.md", "README.md"),
        ("LICENSE", "LICENSE"),
    ):
        original = git(root, "show", f"{UPSTREAM_SHA}:{original_file}")
        require(
            (root / current_file).read_bytes() == original,
            f"{current_file} differs from the pinned upstream import",
        )


def verify_metadata(root: Path) -> None:
    workspace = tomllib.loads((root / "Cargo.toml").read_text(encoding="utf-8"))
    metadata = workspace["workspace"]["package"]
    require(metadata.get("license") == "Apache-2.0", "workspace license mismatch")
    require(metadata.get("repository") == GOREECLOUD_REPOSITORY, "workspace URL mismatch")

    cli = tomllib.loads(
        (root / "crates/obscura-cli/Cargo.toml").read_text(encoding="utf-8")
    )
    binaries = {item["name"]: item["path"] for item in cli["bin"]}
    require(
        binaries.get("obscura") == "src/main.rs",
        "upstream Obscura CLI compatibility target missing",
    )
    require(
        binaries.get("goreecloud-headless-browser") == "src/main.rs",
        "GoreeCloud branded CLI target missing",
    )
    require(
        binaries.get("obscura-worker") == "src/worker.rs",
        "upstream worker target missing",
    )
    cli_source = (root / "crates/obscura-cli/src/main.rs").read_text(encoding="utf-8")
    require(
        'goreecloud-headless-browser' in cli_source,
        "GoreeCloud CLI identity is missing",
    )
    docker = (root / "Dockerfile").read_text(encoding="utf-8")
    require(
        'ENTRYPOINT ["/goreecloud-headless-browser"]' in docker,
        "Docker entry point is not branded",
    )


def verify_workflow_text(contents: str) -> None:
    # Intentionally fail closed if someone adds unreviewed publishing capabilities.
    require(
        bool(re.search(r"(?m)^permissions:\s*\n\s+contents:\s*read\s*$", contents)),
        "CI requires explicit contents: read permissions",
    )
    require(
        bool(re.search(r"(?m)^\s*(?:-\s*)?uses:\s*actions/checkout@" + CHECKOUT_PIN + r"\s*(?:#.*)?$", contents)),
        "CI checkout is not pinned to the reviewed commit",
    )
    require(
        bool(re.search(r"(?m)^\s*persist-credentials:\s*false\s*$", contents)),
        "CI must not persist the checkout token",
    )
    for unsafe in (
        r"(?m)^\s*pull_request_target\s*:",
        r"(?m)^\s*(?:contents|packages|id-token|actions)\s*:\s*write\s*$",
        r"(?m)^\s*(?:publish|deploy|release)\s*:",
        r"\bsecrets\s*\.",
    ):
        require(re.search(unsafe, contents) is None, f"CI contains disallowed marker: {unsafe}")


def verify_workflows(root: Path) -> None:
    directory = root / ".github/workflows"
    active = sorted(
        str(item.relative_to(root))
        for item in directory.iterdir()
        if item.is_file() and item.suffix.lower() in {".yml", ".yaml"}
    )
    require(
        active == [VALIDATION_WORKFLOW],
        f"unexpected active workflows: {active}",
    )
    verify_workflow_text((root / VALIDATION_WORKFLOW).read_text(encoding="utf-8"))


def verify_attribution(root: Path) -> None:
    readme = (root / "README.md").read_text(encoding="utf-8")
    notice = (root / "NOTICE").read_text(encoding="utf-8")
    provenance = (root / "docs/IMPORT_PROVENANCE.md").read_text(encoding="utf-8")
    require(readme.startswith("# GoreeCloud Headless Browser\n"), "product title")
    require("Rebranded Import" in readme, "import classification is missing")
    require("h4ckf0r0day/obscura" in notice, "source attribution is missing")
    require(UPSTREAM_SHA in notice and UPSTREAM_SHA in provenance, "import SHA is missing")
    require("Apache" in (root / "LICENSE").read_text(encoding="utf-8"), "license missing")
    for vendor_license in (
        "vendor/taffy/LICENSE",
        "vendor/wreq-util/LICENSE",
        "vendor/cosmic-text/LICENSE-APACHE",
        "vendor/cosmic-text/LICENSE-MIT",
    ):
        require((root / vendor_license).is_file(), f"missing {vendor_license}")


def main() -> int:
    for title, fn in (
        ("Git ancestry and original source", verify_provenance),
        ("CLI/package metadata", verify_metadata),
        ("attribution and retained licenses", verify_attribution),
        ("read-only CI allowlist", verify_workflows),
    ):
        fn(ROOT)
        print(f"PASS: {title}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"FAIL: {error}") from error
