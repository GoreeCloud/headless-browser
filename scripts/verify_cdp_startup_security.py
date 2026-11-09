#!/usr/bin/env python3
"""Fail-closed CDP startup checks using only disposable local execution.

No public listener is intentionally started. The nonloopback test uses a
nonlocal TEST-NET-1 address (192.0.2.123), never a wildcard interface.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

if __package__:
    from .verify_cdp_loopback_smoke import ROOT, sanitized_env
else:
    from verify_cdp_loopback_smoke import ROOT, sanitized_env


def reject_startup(
    *,
    binary: str,
    host: str,
    token: str | None,
    expected_error: str,
    forwarded: dict[str, str] | None = None,
) -> None:
    path = ROOT / "target/debug" / binary
    if not path.is_file():
        raise AssertionError(f"unbuilt CLI test binary: {binary}")
    environment = sanitized_env(token)
    environment.update(forwarded or {})
    with tempfile.TemporaryDirectory(prefix="goreecloud-rejected-cdp-") as directory:
        ready_path = Path(directory) / "should-not-exist.json"
        command = [
            str(path), "serve", "--host", host, "--port", "0",
            "--workers", "1", "--ready-file", str(ready_path), "--quiet",
        ]
        try:
            outcome = subprocess.run(
                command,
                cwd=ROOT,
                env=environment,
                capture_output=True,
                timeout=8,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise AssertionError("CDP rejected-startup check did not exit promptly") from error

        # Do not print the command, bearer, or captured diagnostics; only a
        # constant error signature confirms the intended fail-closed branch.
        if outcome.returncode == 0 or expected_error.encode("utf-8") not in outcome.stderr:
            raise AssertionError(f"CDP did not enforce expected startup guard for {binary}")
        if ready_path.exists():
            raise AssertionError("refused CDP startup incorrectly published ready file")


def main() -> None:
    reject_startup(
        binary="goreecloud-headless-browser",
        host="192.0.2.123",  # nonlocal RFC5737 documentation address; never binds
        token=None,
        expected_error="refusing to expose CDP without authentication",
    )
    print("PASS: no-token nonloopback CDP startup refused before bind")

    reject_startup(
        binary="obscura",
        host="127.0.0.1",
        token="short-token",
        expected_error="OBSCURA_CDP_TOKEN must be at least 32 bytes",
    )
    print("PASS: compatibility CDP command rejects insufficient bearer length")

    reject_startup(
        binary="goreecloud-headless-browser",
        host="127.0.0.1",
        token=None,
        forwarded={
            "OBSCURA_CDP_FORWARDED_HOST": "0.0.0.0",
            "OBSCURA_CDP_FORWARDED_PORT": "9222",
        },
        expected_error="refusing to expose CDP without authentication",
    )
    print("PASS: forwarded public CDP authority refuses missing authentication")

    reject_startup(
        binary="obscura",
        host="127.0.0.1",
        token=None,
        forwarded={"OBSCURA_CDP_FORWARDED_HOST": "127.0.0.1"},
        expected_error="must be set together",
    )
    print("PASS: partial forwarded CDP configuration rejected")


if __name__ == "__main__":
    main()
