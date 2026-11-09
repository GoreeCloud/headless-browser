# GoreeCloud Headless Browser — dependency and distribution review

**Status: open, unapproved for release.** These are source-inventory facts, not a software bill of materials validated against installed/downloaded artifacts, a vulnerability scan, or license clearance. The primary provenance record remains [IMPORT_PROVENANCE.md](IMPORT_PROVENANCE.md).

## Verified lockfile snapshot (November 9, 2026)

| Source class | Locked packages |
| --- | ---: |
| crates.io registry with syntactically valid SHA-256 checksum fields | 477 |
| Local workspace packages and vendored crates | 13 |
| **Total** | **490** |

The local group consists of ten Obscura workspace crates and three vendored crates: **taffy**, **cosmic-text**, and **wreq-util**. Their Cargo manifest license expressions are recorded by the offline inventory tool, **not** independently legally verified. The 477 registry records have checksums in Cargo.lock; that does **not** prove downloaded source integrity or provide license text. The tracked imported assets directory includes 18 files, including inherited sponsor graphics with separate trademark or copyright questions. Do not assume they are cleared for GoreeCloud redistribution.

## Repeatable local-only review

Run without compiling or fetching dependencies:

    python3 scripts/inventory_cargo_lock.py
    python3 scripts/inventory_cargo_lock.py --json > /tmp/goreecloud-cargo-inventory.json
    python3 -m unittest discover -s tests/goreecloud -p 'test_*.py'

The checker validates Cargo.lock format 4, unique identities, the expected crates.io registry source, correctly shaped registry checksums and correspondence between local manifests and local lock entries. New Git dependencies, alternate registries, missing checksums, unlisted local crates or changed lockfile formats fail closed for review. The JSON representation is deterministic and can be retained as release-candidate input when an approved storage location is selected; CI does not publish an artifact.

**Container:** See [CONTAINER_RELEASE_GATES.md](CONTAINER_RELEASE_GATES.md) for the separate source-only Docker policy and outstanding digest, runtime, image and deployment tests.

## Outstanding before any binary, container or public release

- Compare the **actual downloaded dependency sources and archives** to the lockfile checksums and verify trusted registry/index provenance.
- Retrieve and review third-party license expressions, complete texts, notice and attribution obligations; determine incompatibilities and document decisions.
- Inventory and review font, image, icon, banner, sponsor and other bundled asset rights and trademark risks. Maintain exact upstream attribution.
- Generate and validate a versioned dependency SBOM against the **actual built** artifact and independently scan advisories and vendored source diffs.
- Complete Wardveil build provenance, dependency threat review and container isolation/egress tests, plus GoreeShield privacy/retention acceptance.

A passing inventory check is **not** permission to distribute any source, binaries or images beyond already applicable licenses; it establishes only a reviewable dependency snapshot and fail-closed structural baseline.
