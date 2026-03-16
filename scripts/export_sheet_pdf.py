#!/usr/bin/env python3
"""Export a Google Sheet tab as PDF."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


DEFAULT_EXPORT_PARAMS = {
    "format": "pdf",
    "size": "letter",
    "portrait": "true",
    "fitw": "true",
    "sheetnames": "false",
    "printtitle": "false",
    "pagenum": "UNDEFINED",
    "gridlines": "false",
    "fzr": "false",
}


def parse_google_sheet_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    path_match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", parsed.path)
    if not path_match:
        raise ValueError("Could not find spreadsheet ID in URL")

    sheet_id = path_match.group(1)
    query = parse_qs(parsed.query)

    gid = query.get("gid", [None])[0]
    if gid is None and parsed.fragment.startswith("gid="):
        gid = parsed.fragment.split("=", 1)[1]

    if not gid:
        raise ValueError("Could not find gid in URL")

    return sheet_id, gid


def build_export_url(sheet_id: str, gid: str) -> str:
    params = {**DEFAULT_EXPORT_PARAMS, "gid": gid}
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?{urlencode(params)}"


def download_pdf(export_url: str, output_file: Path) -> None:
    request = Request(
        export_url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Safari/537.36"
        },
    )

    with urlopen(request) as response:
        content = response.read()

    if not content.startswith(b"%PDF"):
        raise RuntimeError(
            "Downloaded file is not a PDF. Ensure the sheet is shared and accessible."
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export a Google Sheet tab to PDF using a share URL."
    )
    parser.add_argument("sheet_url", help="Google Sheets URL containing spreadsheet ID and gid")
    parser.add_argument(
        "--output",
        default="output/sheet-report.pdf",
        help="Path for the generated PDF (default: output/sheet-report.pdf)",
    )

    args = parser.parse_args()

    try:
        sheet_id, gid = parse_google_sheet_url(args.sheet_url)
        export_url = build_export_url(sheet_id, gid)
        download_pdf(export_url, Path(args.output))
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"PDF generated at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
