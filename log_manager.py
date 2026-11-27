"""
Compress old log files and remove old compressed archives.

Usage:
    python log_manager.py [--apply] [--dirs /var/log /tmp/logs]

Without --apply, the script previews the actions.
"""

import argparse
import gzip
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_LOG_DIRS = [
    "/var/log",
    "C:\\Windows\\Logs",
]
COMPRESS_AFTER_DAYS = 7
DELETE_AFTER_DAYS = 30
LOG_FILE = "automation.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
logging.getLogger().addHandler(console)


def compress_file(filepath: Path, dry_run: bool) -> bool:
    """Compress a log file. Return True when the action succeeds or is previewed."""
    gz_path = filepath.with_suffix(filepath.suffix + ".gz")
    if gz_path.exists():
        logging.info("SKIP     Archive already exists: %s", gz_path)
        return False

    if dry_run:
        logging.info("[DRY-RUN] Would compress: %s", filepath)
        return True

    try:
        with filepath.open("rb") as f_in, gzip.open(gz_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        filepath.unlink()
        logging.info("COMPRESS %s  →  %s", filepath.name, gz_path.name)
        return True
    except PermissionError:
        logging.error("PERM-ERR File in use, skipped: %s", filepath)
    except OSError as exc:
        logging.error("OS-ERR   %s | %s", filepath, exc)
    return False


def delete_file(filepath: Path, dry_run: bool) -> bool:
    """Delete an archived log file. Return True when the action succeeds or is previewed."""
    if dry_run:
        logging.info("[DRY-RUN] Would delete:   %s", filepath)
        return True

    try:
        filepath.unlink()
        logging.info("DELETE   %s", filepath)
        return True
    except PermissionError:
        logging.error("PERM-ERR File in use, skipped: %s", filepath)
    except OSError as exc:
        logging.error("OS-ERR   %s | %s", filepath, exc)
    return False


def _modified_at(filepath: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(filepath.stat().st_mtime)
    except OSError as exc:
        logging.error("STAT-ERR %s | %s", filepath, exc)
        return None


def process_directory(directory: str, dry_run: bool) -> dict[str, int]:
    """Compress old .log files and delete old .log.gz archives in one directory tree."""
    stats = {"compressed": 0, "deleted": 0, "errors": 0, "skipped": 0}
    now = datetime.now()
    compress_before = now - timedelta(days=COMPRESS_AFTER_DAYS)
    delete_before = now - timedelta(days=DELETE_AFTER_DAYS)

    path = Path(directory)
    if not path.is_dir():
        logging.warning("DIR-MISS Not a directory or not found: %s", directory)
        return stats

    logging.info("─" * 60)
    logging.info("SCANNING %s", directory)

    for item in path.rglob("*.log"):
        if not item.is_file():
            continue
        modified_at = _modified_at(item)
        if modified_at is None:
            stats["errors"] += 1
            continue
        if modified_at < compress_before:
            archive = item.with_suffix(item.suffix + ".gz")
            if archive.exists():
                logging.info("SKIP     Archive already exists: %s", archive)
                stats["skipped"] += 1
                continue
            ok = compress_file(item, dry_run)
            stats["compressed"] += int(ok)
            stats["errors"] += int(not ok)
        else:
            stats["skipped"] += 1

    for item in path.rglob("*.log.gz"):
        if not item.is_file():
            continue
        modified_at = _modified_at(item)
        if modified_at is None:
            stats["errors"] += 1
            continue
        if modified_at < delete_before:
            ok = delete_file(item, dry_run)
            stats["deleted"] += int(ok)
            stats["errors"] += int(not ok)
        else:
            stats["skipped"] += 1

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Log Manager — compress old logs and remove old archives."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Apply file changes. Preview mode is the default.",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without changing log files (default).",
    )
    parser.add_argument(
        "--dirs",
        nargs="+",
        default=DEFAULT_LOG_DIRS,
        help="Directories to scan (overrides defaults).",
    )
    args = parser.parse_args()
    dry_run = not args.apply

    if dry_run:
        logging.info("════ PREVIEW MODE — pass --apply to change files ════")
    else:
        logging.info("════ APPLY MODE — files may be compressed or deleted ════")

    totals = {"compressed": 0, "deleted": 0, "errors": 0, "skipped": 0}
    for directory in args.dirs:
        result = process_directory(directory, dry_run=dry_run)
        for key in totals:
            totals[key] += result[key]

    logging.info("─" * 60)
    if dry_run:
        logging.info(
            "SUMMARY  Would compress: %d | Would delete: %d | Errors: %d | Skipped: %d",
            totals["compressed"], totals["deleted"], totals["errors"], totals["skipped"],
        )
    else:
        logging.info(
            "SUMMARY  Compressed: %d | Deleted: %d | Errors: %d | Skipped: %d",
            totals["compressed"], totals["deleted"], totals["errors"], totals["skipped"],
        )


if __name__ == "__main__":
    main()
