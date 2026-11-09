"""Pure-Python negative and positive tests for offline Cargo.lock inventory."""

from copy import deepcopy
import unittest

from scripts import inventory_cargo_lock as audit


REGISTRY_ROW = {
    "name": "example-registry",
    "version": "1.2.3",
    "source": audit.REGISTRY,
    "checksum": "a" * 64,
}

LOCAL_ROW = {"name": "local-crate", "version": "0.1.0"}
MANIFESTS = {
    "local-crate": {
        "version": "0.1.0",
        "manifest": "crates/local-crate/Cargo.toml",
        "manifest_license_claim": "Apache-2.0",
    }
}


def mock_lock() -> dict:
    return {"version": 4, "package": [deepcopy(LOCAL_ROW), deepcopy(REGISTRY_ROW)]}


class LockInventoryTests(unittest.TestCase):
    def test_valid_local_and_registry_record(self):
        records = audit.validate_lock(mock_lock(), MANIFESTS)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["name"], "example-registry")
        self.assertEqual(records[1]["manifest_license_claim"], "Apache-2.0")

    def test_rejects_unknown_registry(self):
        lock = mock_lock()
        lock["package"][1]["source"] = "registry+http://untrusted.invalid/index"
        with self.assertRaisesRegex(ValueError, "unreviewed dependency source"):
            audit.validate_lock(lock, MANIFESTS)

    def test_rejects_git_dependencies_unreviewed(self):
        lock = mock_lock()
        lock["package"][1]["source"] = "git+https://example.invalid/repo#abcd"
        with self.assertRaisesRegex(ValueError, "unreviewed dependency source"):
            audit.validate_lock(lock, MANIFESTS)

    def test_rejects_missing_registry_checksum(self):
        lock = mock_lock()
        del lock["package"][1]["checksum"]
        with self.assertRaisesRegex(ValueError, "checksum"):
            audit.validate_lock(lock, MANIFESTS)

    def test_rejects_non_sha256_registry_checksum(self):
        lock = mock_lock()
        lock["package"][1]["checksum"] = "not-hex-sha256"
        with self.assertRaisesRegex(ValueError, "checksum"):
            audit.validate_lock(lock, MANIFESTS)

    def test_rejects_unknown_local_dependency(self):
        lock = mock_lock()
        lock["package"][0]["name"] = "undeclared-local"
        with self.assertRaisesRegex(ValueError, "unrecognized local"):
            audit.validate_lock(lock, MANIFESTS)

    def test_rejects_local_version_drift(self):
        lock = mock_lock()
        lock["package"][0]["version"] = "0.2.0"
        with self.assertRaisesRegex(ValueError, "local version mismatch"):
            audit.validate_lock(lock, MANIFESTS)

    def test_rejects_duplicate_lock_identity(self):
        lock = mock_lock()
        lock["package"].append(deepcopy(REGISTRY_ROW))
        with self.assertRaisesRegex(ValueError, "duplicate Cargo lock"):
            audit.validate_lock(lock, MANIFESTS)

    def test_rejects_unexpected_lock_format(self):
        lock = mock_lock()
        lock["version"] = 3
        with self.assertRaisesRegex(ValueError, "format version"):
            audit.validate_lock(lock, MANIFESTS)

    def test_rejects_missing_local_manifest_in_lockfile(self):
        lock = mock_lock()
        lock["package"] = [deepcopy(REGISTRY_ROW)]
        with self.assertRaisesRegex(ValueError, "local manifest/lockfile drift"):
            audit.validate_lock(lock, MANIFESTS)


if __name__ == "__main__":
    unittest.main()
