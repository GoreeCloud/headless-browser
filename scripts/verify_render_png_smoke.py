#!/usr/bin/env python3
"""Nonpublishing render-feature screenshot smoke on owned-loopback HTML only.

Uses the trusted inert fixture served from 127.0.0.1 and explicit private
network access only for this one known URL. Never contacts public websites.
"""

from __future__ import annotations

import struct
import subprocess
import tempfile
import zlib
from pathlib import Path
from urllib.parse import urlsplit

if __package__:
    from .verify_cdp_owned_dom_smoke import owned_http_page
    from .verify_cdp_loopback_smoke import ROOT, sanitized_env
else:
    from verify_cdp_owned_dom_smoke import owned_http_page
    from verify_cdp_loopback_smoke import ROOT, sanitized_env

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PNG_BYTES = 20 * 1024 * 1024
EXPECTED_VIEWPORT = (1280, 720)


def validate_png(png: bytes) -> tuple[int, int]:
    if not PNG_SIGNATURE == png[:8]:
        raise ValueError("screenshot is not a PNG")
    if len(png) < 33 or len(png) > MAX_PNG_BYTES:
        raise ValueError("PNG size outside reviewed fixture budget")
    if struct.unpack("!I", png[8:12])[0] != 13 or png[12:16] != b"IHDR":
        raise ValueError("missing standard PNG IHDR")
    width, height = struct.unpack("!II", png[16:24])
    if not (1 <= width <= 4096 and 1 <= height <= 4096):
        raise ValueError("unreasonable screenshot dimensions")
    if png[24] not in (8, 16) or png[25] not in (2, 6):
        raise ValueError("unsupported PNG sample depth/color format")
    crc = struct.unpack("!I", png[29:33])[0]
    if zlib.crc32(png[12:29]) != crc:
        raise ValueError("PNG IHDR checksum mismatch")
    if not png.endswith(bytes.fromhex("49454e44ae426082")):
        raise ValueError("PNG is missing the terminating IEND chunk")
    return width, height


def validate_fixture_url(url: str) -> None:
    parsed = urlsplit(url)
    try:
        valid_port = parsed.port is not None and 1 <= parsed.port <= 65535
    except ValueError:
        valid_port = False
    if not (
        parsed.scheme == "http"
        and parsed.hostname == "127.0.0.1"
        and parsed.username is None
        and parsed.password is None
        and valid_port
        and parsed.netloc == f"127.0.0.1:{parsed.port}"
        and parsed.path == "/owned"
        and not parsed.query
        and not parsed.fragment
    ):
        raise ValueError("screenshot smoke is restricted to the owned fixture")


def render_owned_url(url: str, output_path: Path) -> subprocess.CompletedProcess[bytes]:
    validate_fixture_url(url)
    binary = ROOT / "target/debug/goreecloud-headless-browser"
    if not binary.is_file():
        raise AssertionError("render-enabled GoreeCloud CLI executable is missing")
    env = sanitized_env(None)
    for key in ("OBSCURA_SHOT_W", "OBSCURA_SHOT_H", "OBSCURA_SHOT_ANIMATION_TIME_MS",
                "OBSCURA_RENDER_RESOURCE_DEADLINE_MS", "OBSCURA_SHOT_DEVICE_SCALE_FACTOR"):
        env.pop(key, None)
    env["NO_PROXY"] = "127.0.0.1,localhost"
    return subprocess.run(
        [
            str(binary), "--allow-private-network",
            "fetch", "--quiet", "--timeout", "20", "--wait", "1",
            "--screenshot", str(output_path), url,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        timeout=70,
        check=False,
    )


def main() -> None:
    with owned_http_page() as (url, hits), tempfile.TemporaryDirectory(prefix="goreecloud-render-ci-") as folder:
        path = Path(folder) / "trusted-fixture.png"
        result = render_owned_url(url, path)
        if result.returncode != 0:
            # Avoid exposing any future credentials present in diagnostics.
            raise AssertionError("render-enabled GoreeCloud CLI could not screenshot the owned fixture")
        if not path.is_file():
            raise AssertionError("render-enabled CLI did not create a screenshot")
        width, height = validate_png(path.read_bytes())
        if (width, height) != EXPECTED_VIEWPORT:
            raise AssertionError(f"unexpected default screenshot viewport: {width}x{height}")
        if "/owned" not in hits:
            raise AssertionError("screenshot did not request the owned HTML fixture")
        if any(request not in ("/owned", "/favicon.ico") for request in hits):
            raise AssertionError("unexpected owned fixture request during screenshot")

    print("PASS: render-enabled CLI produced valid PNG at expected viewport from owned HTML only")


if __name__ == "__main__":
    main()
