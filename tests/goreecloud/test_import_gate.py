"""Offline regression tests for provenance verification and safe CI allowlisting."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts import verify_goreecloud_import as audit


VALID_CI = f"""name: Offline validation

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  source:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@{audit.CHECKOUT_PIN} # v6
        with:
          persist-credentials: false
      - run: python3 scripts/verify_goreecloud_import.py
"""


class WorkflowGuards(unittest.TestCase):
    def test_pinned_checkout_read_only_passes(self):
        audit.verify_workflow_text(VALID_CI)

    def test_any_extra_workflow_fails_closed(self):
        with TemporaryDirectory() as tmp:
            workflow_dir = Path(tmp) / ".github/workflows"
            workflow_dir.mkdir(parents=True)
            (workflow_dir / "import-validation.yml").write_text(VALID_CI)
            (workflow_dir / "release.yml").write_text("on: push\n")
            with self.assertRaisesRegex(ValueError, "unexpected active workflows"):
                audit.verify_workflows(Path(tmp))

    def test_wrong_checkout_commit_rejected(self):
        with self.assertRaisesRegex(ValueError, "checkout"):
            audit.verify_workflow_text(VALID_CI.replace(audit.CHECKOUT_PIN, "v6"))

    def test_credential_persistence_rejected(self):
        with self.assertRaisesRegex(ValueError, "persist"):
            audit.verify_workflow_text(
                VALID_CI.replace("persist-credentials: false", "persist-credentials: true")
            )

    def test_repo_write_permissions_rejected(self):
        with self.assertRaisesRegex(ValueError, "contents: read"):
            audit.verify_workflow_text(VALID_CI.replace("contents: read", "contents: write"))

    def test_token_secret_expression_rejected(self):
        with self.assertRaisesRegex(ValueError, "disallowed marker"):
            audit.verify_workflow_text(VALID_CI + "\n# ${{ secrets.RELEASE_TOKEN }}\n")

    def test_pull_request_target_rejected(self):
        with self.assertRaisesRegex(ValueError, "disallowed marker"):
            audit.verify_workflow_text(VALID_CI + "\npull_request_target:\n")

    def test_package_write_rejected(self):
        with self.assertRaisesRegex(ValueError, "disallowed marker"):
            audit.verify_workflow_text(VALID_CI + "\npackages: write\n")

    def test_unreviewed_third_party_action_rejected(self):
        with self.assertRaisesRegex(ValueError, "unreviewed"):
            audit.verify_workflow_text(VALID_CI + "\n      - uses: example/action@main\n")

    def test_unpinned_rust_setup_action_rejected(self):
        with self.assertRaisesRegex(ValueError, "unreviewed"):
            audit.verify_workflow_text(VALID_CI + "\n      - uses: dtolnay/rust-toolchain@stable\n")

    def test_pinned_rust_setup_action_allowed(self):
        audit.verify_workflow_text(
            VALID_CI + f"\n      - uses: dtolnay/rust-toolchain@{audit.RUST_TOOLCHAIN_PIN}\n"
        )

    def test_second_checkout_without_credentials_false_rejected(self):
        with self.assertRaisesRegex(ValueError, "every checkout"):
            audit.verify_workflow_text(
                VALID_CI + f"\n      - uses: actions/checkout@{audit.CHECKOUT_PIN}\n"
            )

    def test_other_permission_write_rejected(self):
        with self.assertRaisesRegex(ValueError, "disallowed marker"):
            audit.verify_workflow_text(VALID_CI + "\npull-requests: write\n")

    def test_write_all_rejected(self):
        with self.assertRaisesRegex(ValueError, "disallowed marker"):
            audit.verify_workflow_text(VALID_CI + "\npermissions: write-all\n")

    def test_event_privilege_upgrade_rejected(self):
        with self.assertRaisesRegex(ValueError, "disallowed marker"):
            audit.verify_workflow_text(VALID_CI + "\nworkflow_run:\n")

    def test_original_source_commit_is_pinned(self):
        self.assertEqual(audit.UPSTREAM_SHA, "59276a3620aed0320879f60b9f049010d568088c")


if __name__ == "__main__":
    unittest.main()
