#!/usr/bin/env python3
"""Real CDP HTTP control-plane smoke on 127.0.0.1 only, no external browsing.

Uses development-only executables built by GitHub Actions. This is not a
WebSocket/CDP command, JS, page-rendering, sandbox or remote-access acceptance.
"""

from __future__ import annotations

import http.client
import json
import os
import secrets
import socket
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]


def sanitized_env(token: str | None) -> dict[str, str]:
    environ = os.environ.copy()
    for name in (
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy",
        "all_proxy", "OBSCURA_PROXY", "OBSCURA_CDP_TOKEN",
        "OBSCURA_CDP_FORWARDED_HOST", "OBSCURA_CDP_FORWARDED_PORT",
    ):
        environ.pop(name, None)
    environ["NO_PROXY"] = "127.0.0.1,localhost"
    environ["OBSCURA_ALLOW_PRIVATE_NETWORK"] = "0"
    environ["RUST_LOG"] = "off"
    if token is not None:
        environ["OBSCURA_CDP_TOKEN"] = token
    return environ


def validate_ready(record: object, expected_pid: int) -> int:
    if not isinstance(record, dict):
        raise AssertionError("ready record is not an object")
    if record.get("pid") != expected_pid or record.get("host") != "127.0.0.1":
        raise AssertionError("ready record has unexpected process or nonloopback bind")
    port = record.get("port")
    if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
        raise AssertionError("ready record has invalid port")
    if record.get("websocket_path") != "/devtools/browser":
        raise AssertionError("ready record has unexpected browser endpoint")
    return port


@contextmanager
def disposable_cdp_server(
    name: str, token: str | None = None, *, allow_private_network: bool = False
) -> Iterator[int]:
    binary = ROOT / "target/debug" / name
    if not binary.is_file():
        raise AssertionError(f"CDP binary was not built: {binary}")

    with tempfile.TemporaryDirectory(prefix="goreecloud-owned-cdp-") as directory:
        ready = Path(directory) / "ready.json"
        proc = subprocess.Popen(
            [
                str(binary),
                *(["--allow-private-network"] if allow_private_network else []),
                "serve", "--host", "127.0.0.1",
                "--port", "0", "--workers", "1", "--ready-file", str(ready),
                "--quiet",
            ],
            cwd=ROOT,
            env=sanitized_env(token),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 30
            while not ready.is_file():
                if proc.poll() is not None:
                    raise AssertionError(f"{name} CDP server exited before readiness (rc={proc.returncode})")
                if time.monotonic() >= deadline:
                    raise AssertionError(f"{name} CDP readiness exceeded 30 seconds")
                time.sleep(0.1)
            record = json.loads(ready.read_text(encoding="utf-8"))
            port = validate_ready(record, proc.pid)
            if os.name == "posix":
                mode = ready.stat().st_mode & 0o777
                if mode != 0o600:
                    raise AssertionError(f"insecure CDP ready-file mode: {oct(mode)}")
            # Readiness is published before the accept thread starts. Probe
            # briefly with a bounded loop rather than assuming instant accept.
            for _ in range(40):
                try:
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
                    connection.connect()
                    connection.close()
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise AssertionError("CDP ready file exists but loopback port is unreachable")
            yield port
        finally:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


def get_version(port: int, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", "/json/version", headers=headers or {})
        result = connection.getresponse()
        return result.status, result.read(65536)
    finally:
        connection.close()


def raw_get_version(port: int, header_lines: list[str]) -> tuple[int, bytes]:
    # http.client's dict API intentionally cannot represent duplicate
    # headers; send a bounded, literal test request to owned loopback instead.
    request = ("\r\n".join([
        "GET /json/version HTTP/1.1",
        *header_lines,
        "Connection: close",
        "",
        "",
    ])).encode("ascii")
    if len(request) > 2048:
        raise AssertionError("raw HTTP smoke request exceeded expected bound")
    with socket.create_connection(("127.0.0.1", port), timeout=5) as stream:
        stream.settimeout(5)
        stream.sendall(request)
        response = http.client.HTTPResponse(stream)
        response.begin()
        return response.status, response.read(4096)


def require_rejected_raw(port: int, header_lines: list[str], status: int) -> None:
    found, body = raw_get_version(port, header_lines)
    if found != status or b"error" not in body:
        raise AssertionError(f"expected duplicate-header HTTP {status} refusal, got {found}")


def require_version(port: int, headers: dict[str, str] | None = None) -> None:
    status, body = get_version(port, headers)
    if status != 200:
        raise AssertionError(f"local CDP discovery refused expected client (status={status})")
    value = json.loads(body)
    expected = f"ws://127.0.0.1:{port}/devtools/browser"
    if value.get("webSocketDebuggerUrl") != expected:
        raise AssertionError("CDP discovery returned an unexpected WebSocket authority")
    if value.get("Protocol-Version") != "1.3":
        raise AssertionError("CDP discovery returned an unexpected protocol version")


def require_rejected(port: int, headers: dict[str, str], status: int) -> None:
    found, body = get_version(port, headers)
    if found != status or b"error" not in body:
        raise AssertionError(f"expected HTTP {status} refusal, got {found}")


def main() -> None:
    with disposable_cdp_server("goreecloud-headless-browser") as port:
        require_version(port)
        require_rejected(port, {"Host": "malicious.invalid"}, 403)
        require_rejected(port, {"Origin": "https://malicious.invalid"}, 403)
        require_rejected_raw(port, [
            f"Host: 127.0.0.1:{port}",
            f"hOsT: 127.0.0.1:{port}",
        ], 403)
        require_rejected_raw(port, [
            f"Host: 127.0.0.1:{port}",
            "Origin: https://malicious.invalid",
            "origin: https://other.invalid",
        ], 403)
        # A Host is an authority only: reject URL userinfo and components
        # even when the resolved host would otherwise match 127.0.0.1.
        for malformed in (
            f"attacker@127.0.0.1:{port}",
            f"user:password@127.0.0.1:{port}",
            f"127.0.0.1:{port}/hidden",
            f"127.0.0.1:{port}?query=1",
            f"127.0.0.1:{port}#fragment",
        ):
            require_rejected(port, {"Host": malformed}, 403)
    print("PASS: local GoreeCloud CDP discovery; foreign/malformed Host and Origin rejected")

    bearer = secrets.token_urlsafe(32)
    with disposable_cdp_server("obscura", bearer) as port:
        require_rejected(port, {}, 401)
        require_rejected(port, {"Authorization": "Bearer wrong-token"}, 401)
        require_rejected_raw(port, [
            f"Host: 127.0.0.1:{port}",
            f"Authorization: Bearer {bearer}",
            f"authorization: Bearer {bearer}",
        ], 401)
        require_version(port, {"Authorization": f"Bearer {bearer}"})
        require_rejected(
            port,
            {"Origin": "https://malicious.invalid", "Authorization": f"Bearer {bearer}"},
            403,
        )
    print("PASS: local Obscura CDP bearer authentication and browser-Origin refusal")


if __name__ == "__main__":
    main()
