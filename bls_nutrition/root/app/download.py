"""BLS 4.0 data download."""

from __future__ import annotations

import html
import json
import re
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

DOWNLOAD_PAGE = "https://blsdb.de/download"
GOVDATA_URL = (
    "https://www.govdata.de/suche/daten/"
    "bundeslebensmittelschlussel-bls-version-4-0-deutsche-nahrstoffdatenbank"
)
DEBUG_LOG_PATH = Path("/Users/henry/Projects/hassio-addons/.cursor/debug-92f7bb.log")


def _debug_log(
    hypothesis_id: str, location: str, message: str, data: dict[str, object] | None = None
) -> None:
    payload = {
        "sessionId": "92f7bb",
        "runId": "run1",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
    }
    try:
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except OSError:
        pass


def _extract_zip_link(html_text: str) -> str | None:
    decoded = html.unescape(html_text)
    patterns = [
        r'href="(/assets/uploads/[^"]+\.zip[^"]*)"',
        r'href="(https?://[^"]+\.zip[^"]*)"',
        r'href="([^"]+\.zip[^"]*)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, decoded, re.IGNORECASE)
        if match:
            link = match.group(1)
            if link.startswith("http"):
                return link
            return f"https://blsdb.de{link}"
    return None


def download_bls_archive(dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / "bls_4_0.zip"
    started = time.monotonic()
    print(f"[bls-debug] download enter t=0.0s dest={dest_dir}")

    # #region agent log
    _debug_log("H3", "download.py:66", "download_bls_archive_start", {"dest_dir": str(dest_dir)})
    # #endregion
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        response = client.get(DOWNLOAD_PAGE)
        response.raise_for_status()
        print(f"[bls-debug] download page fetched t={time.monotonic()-started:.1f}s")
        zip_url = _extract_zip_link(response.text)
        if not zip_url:
            raise RuntimeError("Could not find BLS download link on blsdb.de/download")

        # #region agent log
        _debug_log("H3", "download.py:75", "download_zip_stream_start", {"zip_url": zip_url})
        # #endregion
        print(f"[bls-download] Fetching {zip_url}")
        with client.stream("GET", zip_url) as stream:
            stream.raise_for_status()
            with zip_path.open("wb") as handle:
                for chunk in stream.iter_bytes():
                    handle.write(chunk)
        print(f"[bls-debug] zip stream fetched t={time.monotonic()-started:.1f}s")

    # #region agent log
    _debug_log("H3", "download.py:84", "download_bls_archive_done", {"zip_path": str(zip_path)})
    # #endregion
    return zip_path


def extract_bls_files(zip_path: Path, dest_dir: Path) -> tuple[Path, Path | None]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    data_file: Path | None = None
    components_file: Path | None = None

    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(dest_dir)
        for member in archive.namelist():
            lower = member.lower()
            if lower.endswith(".xlsx") and "daten" in lower:
                data_file = dest_dir / member
            if lower.endswith(".xlsx") and "components" in lower:
                components_file = dest_dir / member

    if data_file is None:
        for path in dest_dir.rglob("*.xlsx"):
            lower = path.name.lower()
            if "daten" in lower:
                data_file = path
            elif "components" in lower:
                components_file = path

    if data_file is None or not data_file.exists():
        raise RuntimeError("BLS data XLSX not found in downloaded archive")

    return data_file, components_file
