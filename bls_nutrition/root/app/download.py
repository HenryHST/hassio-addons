"""BLS 4.0 data download."""

from __future__ import annotations

import html
import json
import re
import time
import zipfile
from pathlib import Path

import httpx

DOWNLOAD_PAGE = "https://blsdb.de/download"
DEBUG_LOG_PATH = Path("/data/debug-92f7bb.log")
GOVDATA_URL = (
    "https://www.govdata.de/suche/daten/"
    "bundeslebensmittelschlussel-bls-version-4-0-deutsche-nahrstoffdatenbank"
)


def _debug_log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    # #region agent log
    payload = {
        "sessionId": "92f7bb",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    for log_path in (DEBUG_LOG_PATH, Path("/Users/henry/Projects/hassio-addons/.cursor/debug-92f7bb.log")):
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")
            break
        except OSError:
            continue
    # #endregion


def _extract_zip_link(html_text: str) -> str | None:
    decoded = html.unescape(html_text)
    # #region agent log
    _debug_log(
        "A",
        "download.py:_extract_zip_link",
        "html entity analysis",
        {
            "has_literal_dot_zip": ".zip" in html_text,
            "has_entity_dot_zip": "&#46;zip" in html_text,
            "has_decoded_assets_zip": "/assets/uploads/" in decoded and ".zip" in decoded,
        },
    )
    # #endregion

    patterns = [
        r'href="(/assets/uploads/[^"]+\.zip[^"]*)"',
        r'href="(https?://[^"]+\.zip[^"]*)"',
        r'href="([^"]+\.zip[^"]*)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, decoded, re.IGNORECASE)
        if match:
            link = match.group(1)
            final = link if link.startswith("http") else f"https://blsdb.de{link}"
            # #region agent log
            _debug_log(
                "A",
                "download.py:_extract_zip_link",
                "matched zip link",
                {"pattern": pattern, "link": final},
            )
            # #endregion
            return final

    # #region agent log
    _debug_log(
        "B",
        "download.py:_extract_zip_link",
        "no zip link matched",
        {"decoded_snippet": decoded[decoded.find("Download BLS-Daten") - 120 : decoded.find("Download BLS-Daten") + 120] if "Download BLS-Daten" in decoded else ""},
    )
    # #endregion
    return None


def download_bls_archive(dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / "bls_4_0.zip"

    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        response = client.get(DOWNLOAD_PAGE)
        response.raise_for_status()
        # #region agent log
        _debug_log(
            "D",
            "download.py:download_bls_archive",
            "download page fetched",
            {
                "status_code": response.status_code,
                "final_url": str(response.url),
                "content_length": len(response.text),
            },
        )
        # #endregion
        zip_url = _extract_zip_link(response.text)
        if not zip_url:
            raise RuntimeError("Could not find BLS download link on blsdb.de/download")

        print(f"[bls-download] Fetching {zip_url}")
        # #region agent log
        _debug_log(
            "C",
            "download.py:download_bls_archive",
            "starting zip download",
            {"zip_url": zip_url},
        )
        # #endregion
        with client.stream("GET", zip_url) as stream:
            stream.raise_for_status()
            with zip_path.open("wb") as handle:
                for chunk in stream.iter_bytes():
                    handle.write(chunk)

    # #region agent log
    _debug_log(
        "C",
        "download.py:download_bls_archive",
        "zip download complete",
        {"zip_path": str(zip_path), "size_bytes": zip_path.stat().st_size},
    )
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
