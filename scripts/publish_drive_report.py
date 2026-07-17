#!/usr/bin/env python3
"""Create a print PDF from a Cricket Markdown report and upload it to Google Drive."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from cricket.config import DEFAULT_CONFIG_PATH, load_config


def report_date(report_path: Path) -> str:
    suffix = "_crosstrek_search_report.md"
    if not report_path.name.endswith(suffix):
        raise ValueError("Expected a Cricket report named YYYY-MM-DD_crosstrek_search_report.md")
    return report_path.name[: -len(suffix)]


def wsl_path(flag: str, path: Path) -> str:
    return subprocess.run(
        ["wslpath", flag, str(path)], check=True, capture_output=True, text=True
    ).stdout.strip()


def publish(report_path: Path, config_path: Path) -> str:
    config = load_config(config_path)
    drive = config.get("publishing", {}).get("google_drive", {})
    remote = drive.get("remote")
    folder_id = drive.get("folder_id")
    chrome_path = drive.get("chrome_path")
    if not remote or not folder_id or not chrome_path:
        raise ValueError("publishing.google_drive requires remote, folder_id, and chrome_path")

    date = report_date(report_path)
    filename = "%s cricket report.pdf" % date
    renderer = Path(__file__).with_name("render_web_report.py")

    with tempfile.TemporaryDirectory(prefix="cricket-drive-") as temporary_dir:
        temporary_path = Path(temporary_dir)
        html_path = temporary_path / "report.html"
        pdf_path = temporary_path / filename
        subprocess.run(["python3", str(renderer), str(report_path), "--output", str(html_path)], check=True)

        html_url = "file:%s" % wsl_path("-m", html_path)
        pdf_windows_path = wsl_path("-w", pdf_path)
        subprocess.run(
            [
                chrome_path,
                "--headless",
                "--disable-gpu",
                "--no-pdf-header-footer",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=5000",
                "--print-to-pdf=%s" % pdf_windows_path,
                html_url,
            ],
            check=True,
        )
        subprocess.run(
            [
                "rclone",
                "copyto",
                "--drive-root-folder-id",
                folder_id,
                str(pdf_path),
                "%s:%s" % (remote, filename),
            ],
            check=True,
        )
    return filename


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Markdown report to publish")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    print("Cricket copied %s to the family Google Drive folder." % publish(args.report, args.config))


if __name__ == "__main__":
    main()
