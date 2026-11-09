"""No-network unit checks for Cargo metadata target expectations."""

import unittest

from scripts.verify_cargo_targets import validate_metadata


def manifest(*targets):
    return {
        "packages": [{
            "name": "obscura-cli",
            "targets": [
                {"name": name, "src_path": f"/code/src/{path}", "kind": ["bin"]}
                for name, path in targets
            ],
        }],
    }


class CliManifestValidationTests(unittest.TestCase):
    def test_retains_upstream_and_goreecloud_binaries(self):
        validate_metadata(manifest(
            ("goreecloud-headless-browser", "main.rs"),
            ("obscura", "main.rs"),
            ("obscura-worker", "worker.rs"),
        ))

    def test_missing_legacy_binary_fails(self):
        with self.assertRaisesRegex(ValueError, "obscura"):
            validate_metadata(manifest(
                ("goreecloud-headless-browser", "main.rs"),
                ("obscura-worker", "worker.rs"),
            ))

    def test_wrong_worker_source_fails(self):
        with self.assertRaisesRegex(ValueError, "obscura-worker"):
            validate_metadata(manifest(
                ("goreecloud-headless-browser", "main.rs"),
                ("obscura", "main.rs"),
                ("obscura-worker", "main.rs"),
            ))

    def test_missing_package_fails(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            validate_metadata({"packages": []})

    def test_non_bin_target_is_not_accepted(self):
        with self.assertRaisesRegex(ValueError, "Expected binary"):
            validate_metadata({
                "packages": [{
                    "name": "obscura-cli",
                    "targets": [
                        {"name": "goreecloud-headless-browser", "src_path": "/src/main.rs", "kind": ["lib"]},
                    ],
                }],
            })


if __name__ == "__main__":
    unittest.main()
