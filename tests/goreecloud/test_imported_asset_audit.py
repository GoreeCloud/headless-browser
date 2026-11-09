"""Regression tests for bit-for-bit inherited asset inventory and rights gating."""

import unittest
from pathlib import Path
from unittest import mock

from scripts import verify_imported_assets as audit


class UpstreamAssetAuditTests(unittest.TestCase):
    def test_snapshot_matches_original_upstream(self):
        records = audit.verify_asset_tree()
        self.assertEqual(len(records), 18)
        self.assertEqual(sum(r["category"] == "inherited_sponsor_graphic" for r in records), 16)
        self.assertEqual(sum(r["category"] == "inherited_obscura_brand_graphic" for r in records), 2)
        self.assertTrue(all(r["redistribution_rights_verified"] == "no" for r in records))
        self.assertTrue(all(r["trademark_use_verified"] == "no" for r in records))

    def test_missing_banner_is_rejected(self):
        names = set(audit.upstream_entries(audit.ROOT)) - {"assets/banner.png"}
        with self.assertRaisesRegex(ValueError, "count"):
            audit.assert_expected_assets(names)

    def test_new_sponsor_is_rejected(self):
        names = set(audit.upstream_entries(audit.ROOT)) | {"assets/sponsors/unreviewed.png"}
        with self.assertRaisesRegex(ValueError, "count"):
            audit.assert_expected_assets(names)

    def test_unreviewed_file_root_is_rejected(self):
        names = set(audit.upstream_entries(audit.ROOT))
        names.remove("assets/sponsors/9proxy.gif")
        names.add("assets/new-unreviewed.png")
        with self.assertRaisesRegex(ValueError, "sponsor graphic"):
            audit.assert_expected_assets(names)

    def test_newly_added_asset_requires_rights_review(self):
        original = audit.git

        def with_new_asset(root: Path, *args: str) -> bytes:
            if args[:4] == ("ls-files", "-z", "--others", "--exclude-standard"):
                return b"assets/new_image.png\x00"
            return original(root, *args)

        with mock.patch.object(audit, "git", side_effect=with_new_asset):
            with self.assertRaisesRegex(ValueError, "untracked assets"):
                audit.verify_asset_tree()

    def test_mutated_graphic_requires_review(self):
        original = audit.git

        def altered_source(root: Path, *args: str) -> bytes:
            if len(args) == 2 and args[0] == "show" and args[1].endswith("assets/banner.png"):
                return b"unexpected-changed-asset-content"
            return original(root, *args)

        with mock.patch.object(audit, "git", side_effect=altered_source):
            with self.assertRaisesRegex(ValueError, "asset was changed"):
                audit.verify_asset_tree()


if __name__ == "__main__":
    unittest.main()
