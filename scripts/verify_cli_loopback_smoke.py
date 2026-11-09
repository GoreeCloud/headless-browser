#!/usr/bin/env python3
"""Nonpublishing, owned-loopback executable smoke test (stdlib only).

Only used with binaries built from the checked-out GoreeCloud source on an
isolated CI runner. Does not navigate any external website.
"""

from __future__ import annotations

import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = bytes([0]) + b"GoreeCloud local fixture" + bytes([255, 13, 10]) + b"raw bytes preserved" + bytes([0])
BINARIES = ("goreecloud-headless-browser", "obscura")


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.server.hits.append(self.path)  # type: ignore[attr-defined]
        if self.path != "/fixture":
            self.send_error(404, "fixture not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)

    def log_message(self, format: str, *args: object) -> None:
        pass  # Fixture contains no requests or secrets worth logging.


class LocalFixture:
    def __init__(self) -> None:
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None

    def __enter__(self) -> "LocalFixture":
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        self.server.hits = []  # type: ignore[attr-defined]
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True, name="owned-loopback-fixture"
        )
        self.thread.start()
        return self

    @property
    def url(self) -> str:
        assert self.server is not None
        return f"http://127.0.0.1:{self.server.server_port}/fixture"

    @property
    def hits(self) -> list[str]:
        assert self.server is not None
        return self.server.hits  # type: ignore[attr-defined]

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=5)


def launch(binary: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    # Explicitly suppress inherited proxy env and keep the deny guard enabled
    # unless the invocation explicitly passes the trusted-fixture opt-in.
    environ = os.environ.copy()
    for name in (
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy",
        "all_proxy", "OBSCURA_PROXY",
    ):
        environ.pop(name, None)
    environ["NO_PROXY"] = "127.0.0.1,localhost"
    environ["OBSCURA_ALLOW_PRIVATE_NETWORK"] = "0"
    environ["RUST_LOG"] = "off"
    return subprocess.run(
        [str(binary), *args],
        cwd=ROOT,
        env=environ,
        capture_output=True,
        timeout=25,
        check=False,
    )


def validate_binary_names() -> None:
    for name in BINARIES:
        path = ROOT / "target/debug" / name
        if not path.is_file():
            raise AssertionError(f"missing built executable: {path}")
        result = launch(path, "--help")
        if result.returncode != 0 or f"Usage: {name}".encode() not in result.stdout:
            raise AssertionError(
                f"{name} --help identity mismatch (rc={result.returncode}): "
                f"{result.stdout[:300]!r} {result.stderr[:300]!r}"
            )
        print(f"PASS: built {name} --help retains its own command name")


def validate_private_network_guard() -> None:
    with LocalFixture() as fixture:
        binary = ROOT / "target/debug/goreecloud-headless-browser"
        denied = launch(
            binary, "fetch", "--dump", "original", "--timeout", "10",
            "--quiet", fixture.url
        )
        if denied.returncode == 0:
            raise AssertionError("default SSRF guard unexpectedly allowed loopback")
        if fixture.hits:
            raise AssertionError("blocked loopback request nevertheless reached fixture")
        print("PASS: default CLI SSRF policy rejected loopback without network request")

        for name in BINARIES:
            result = launch(
                ROOT / "target/debug" / name,
                "--allow-private-network",
                "fetch", "--dump", "original", "--timeout", "10",
                "--quiet", fixture.url,
            )
            if result.returncode != 0:
                raise AssertionError(
                    f"{name} explicit owned-fixture opt-in failed "
                    f"(rc={result.returncode}): {result.stderr[:500]!r}"
                )
            if result.stdout != PAYLOAD:
                raise AssertionError(
                    f"{name} altered raw fixture bytes "
                    f"(expected={PAYLOAD!r}, got={result.stdout[:200]!r})"
                )
        if fixture.hits != ["/fixture", "/fixture"]:
            raise AssertionError(f"unexpected fixture request trace: {fixture.hits!r}")
        print("PASS: both CLI binaries fetch exact bytes from the opt-in owned fixture")


def main() -> None:
    validate_binary_names()
    validate_private_network_guard()


if __name__ == "__main__":
    main()
