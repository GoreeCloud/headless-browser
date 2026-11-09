"""Offline regression checks for a reviewed development-only container recipe."""

import unittest
from pathlib import Path

from scripts import verify_container_source_policy as audit

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")
CDP = (ROOT / "crates/obscura-cdp/src/server.rs").read_text(encoding="utf-8")


class ContainerSourcePolicyTests(unittest.TestCase):
    def validate(self, changed: str, error: str):
        with self.assertRaisesRegex(ValueError, error):
            audit.verify_dockerfile(changed, CDP)

    def test_current_nonpublishing_docker_recipe_matches_policy(self):
        audit.verify_dockerfile(DOCKERFILE, CDP)

    def test_cdp_auth_guard_must_not_disappear(self):
        with self.assertRaisesRegex(ValueError, "authentication"):
            audit.verify_dockerfile(DOCKERFILE, "")

    def test_root_runtime_image_not_allowed(self):
        self.validate(
            DOCKERFILE.replace("cc-debian12:nonroot", "cc-debian12:latest"),
            "nonroot",
        )

    def test_runtime_user_cannot_override_nonroot(self):
        self.validate(DOCKERFILE + "\nUSER root\n", "runtime USER")

    def test_embedded_token_rejected(self):
        self.validate(DOCKERFILE + "\nENV OBSCURA_CDP_TOKEN=placeholder\n", "secret")

    def test_private_network_optin_rejected(self):
        self.validate(DOCKERFILE + "\nENV OBSCURA_ALLOW_PRIVATE_NETWORK=1\n", "private-network")

    def test_unreviewed_add_rejected(self):
        self.validate(DOCKERFILE + "\nADD https://invalid.test/payload /tmp/payload\n", "ADD")

    def test_actual_source_build_must_propagate_failure(self):
        changed = DOCKERFILE.replace(
            "touch crates/*/src/*.rs && cargo build --release",
            "touch crates/*/src/*.rs && cargo build --release --broken || true",
        )
        self.assertNotEqual(changed, DOCKERFILE)
        self.validate(changed, "unmasked")

    def test_container_executable_must_remain_branded(self):
        changed = DOCKERFILE.replace(
            'ENTRYPOINT ["/goreecloud-headless-browser"]',
            'ENTRYPOINT ["/obscura"]',
        )
        self.validate(changed, "entrypoint")

    def test_worker_binary_cannot_be_omitted(self):
        line = "COPY --from=builder /build/target/release/obscura-worker /obscura-worker"
        self.assertIn(line, DOCKERFILE)
        self.validate(DOCKERFILE.replace(line, ""), "missing container binary")

    def test_extra_docker_stage_requires_review(self):
        self.validate(DOCKERFILE + "\nFROM alpine:latest\n", "stages")

    def test_unterminated_continuation_rejected(self):
        with self.assertRaisesRegex(ValueError, "unfinished"):
            audit.instructions("FROM rust:1-slim-bookworm AS builder\nRUN something \\")


if __name__ == "__main__":
    unittest.main()
