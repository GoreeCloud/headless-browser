# GoreeCloud Headless Browser — inherited graphic provenance and rights review

**Status: exact source provenance verified; redistribution/trademark permissions NOT independently verified.**

On November 9, 2026, all 18 tracked binary/image resources in `assets/` were compared **byte-for-byte** against the attributed Obscura upstream commit `59276a3620aed0320879f60b9f049010d568088c`. The files remain inherited source assets; neither exact provenance nor the imported workspace Apache-2.0 license establishes separate rights to sponsor or original brand imagery.

The 16 `assets/sponsors/` graphics include third-party sponsor and proxy-provider names/logos; two graphics at `assets/banner.png` and `assets/icon.png` represent imported Obscura branding. GoreeCloud must not infer third-party sponsorship, endorsement, trademark licenses, or assignment of these files. Do not repurpose them as GoreeCloud product branding or bundled marketing material without specific rights review.

## Pinned, read-only source snapshot

| Imported path | Class | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `assets/banner.png` | Upstream brand graphic — permissions unverified | 34,239 | `b0791af9e13bec375527605c04d4693b71f62a3abb85b57d3cce0cc6ca7e3d15` |
| `assets/icon.png` | Upstream brand graphic — permissions unverified | 13,992 | `2d6646c22668454986891e53a397023bfbf8854c55a74e1539bdf6cd8a2ba7bc` |
| `assets/sponsors/9proxy.gif` | Sponsor graphic — permissions unverified | 2,260,371 | `bcdb94559d83f8138762e4c782278cac8b3ed5dc7c26eb811afb6d7cbc283ed4` |
| `assets/sponsors/9proxy.png` | Sponsor graphic — permissions unverified | 18,509 | `4a31b10e760b0a34994dbe6a3e5e4dfdf041638af128953ad8a3fb37c2cb96a5` |
| `assets/sponsors/Masklabs.png` | Sponsor graphic — permissions unverified | 334,593 | `b6ff56fa3b9225c9bcf91b0627ccfb93971f14458d68262b0216a04ecc986dca` |
| `assets/sponsors/mangoproxy.png` | Sponsor graphic — permissions unverified | 510,474 | `3150f06f70ee919bdf6131e66c8c0fafc38aa4cc70d84a06236966a62a452ea9` |
| `assets/sponsors/niuproxlogo.png` | Sponsor graphic — permissions unverified | 14,147 | `c1e6e4f3a5d20a88a792c516b58a89e6e1b174d44510d1bedd55ebdd45976bd7` |
| `assets/sponsors/niuproxy-logo.png` | Sponsor graphic — permissions unverified | 30,579 | `c25a70b4e9f676deba722e6f66e2a2fb36b30b09f2302aed575e15b69bba32e5` |
| `assets/sponsors/nodemaven.svg` | Sponsor graphic — permissions unverified | 30,066 | `ece234dcc88a039bc0ff64d8821a08fe0cc5c57114967cb769e516bea2f8c9c7` |
| `assets/sponsors/nodemaven2.png` | Sponsor graphic — permissions unverified | 95,907 | `6a406f8d9bd64798291d8a88e7765652dc3531d7c8e7a9d94fd76e5fe12b49c9` |
| `assets/sponsors/nodemaven3.png` | Sponsor graphic — permissions unverified | 193,599 | `82ca8bcca61e0634475b093873e695dd445dacb8416f1c7b41c5d6e1822b5c9d` |
| `assets/sponsors/nodemaven4.png` | Sponsor graphic — permissions unverified | 279,390 | `c216b197415041bf8272bd35e6383cd1ebf2b02cb60bbf07e5092fb61908cf72` |
| `assets/sponsors/proxyempire.png` | Sponsor graphic — permissions unverified | 8,765 | `19ee14abba2c67645480b97ebab218f71e4b4feb3b8e816d019e8e1428be4922` |
| `assets/sponsors/rapidproxy.png` | Sponsor graphic — permissions unverified | 16,540 | `fde68ab11f66b4726041c40c4b7ecd8a12e1ce2146062c24064bcdada70c8a83` |
| `assets/sponsors/swiftproxy.png` | Sponsor graphic — permissions unverified | 335,576 | `1b2b88550d89c1c40dcc26cab2106120eba55c13f22eb7de63b7e7a090ab7833` |
| `assets/sponsors/swiftproxy2.png` | Sponsor graphic — permissions unverified | 7,786 | `1a18b940d4fea66bac01493e4d72e93fcbb1687aec1048bb122e5c87c4600a48` |
| `assets/sponsors/sxproxy.png` | Sponsor graphic — permissions unverified | 2,929 | `27e1c9d2f2a5dd1886ebef7ff4b5a368d6625b0546780391ee5bc4f220438ae2` |
| `assets/sponsors/thordatalogo.png` | Sponsor graphic — permissions unverified | 3,592 | `6fa8efcedc20c0313c8b90c310dd2d5bb5f29f80f02034b1e7c0a4f326ecb5b0` |

## Controls and limitations

- `python3 scripts/verify_imported_assets.py` checks that all 18 imported assets are unmodified, there are no missing or new tracked/untracked assets, and no symlinks. It compares the bytes with the **pinned upstream Git object**, without network calls or executing inherited scripts. `--json` emits a deterministic local provenance ledger; CI does not publish it.
- The repository import preserves the upstream Git history and Apache-2.0 `LICENSE` and `NOTICE`, but third-party image license terms, permission grants and logos have **not** been independently obtained or reviewed.
- Before a public binary/container/website redistribution, review each graphic for copyright, trademarks, attribution requirements, approved usage and endorsement restrictions. If no rights evidence exists, exclude it from distributable branding/marketing assets rather than presuming permission.
- This source snapshot does not detect vulnerabilities, verify font licenses, audit all third-party code, authorize distribution of sponsor media, or imply that GoreeCloud is affiliated with the named companies.
- Source-policy updates must be reviewed on a dedicated PR with updated evidence. If upstream assets are deliberately removed later after legal review, the source allowlist and this record must be changed **together**; no blind rebranding.

For dependency licensing and container gates, also see [SUPPLY_CHAIN_REVIEW.md](SUPPLY_CHAIN_REVIEW.md) and [CONTAINER_RELEASE_GATES.md](CONTAINER_RELEASE_GATES.md). The release tracker is [Issue #2](https://github.com/GoreeCloud/headless-browser/issues/2).
