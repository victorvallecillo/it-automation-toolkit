"""
log_manager.py
==============
Scans defined log directories, compresses files older than 7 days,
and deletes those older than 30 days.

Usage:
    python log_manager.py [--dry-run] [--dirs /var/log /tmp/logs]

Author: IT Automation Toolkit
"""

import os
import gzip
import shutil
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
DEFAULT_LOG_DIRS = [
    "/var/log",          # Linux
    "C:\\Windows\\Logs", # Windows Server
]
COMPRESS_AFTER_DAYS = 7
DELETE_AFTER_DAYS   = 30
LOG_FILE            = "automation.log"

# ──────────────────────────────────────────────
# Logging setup
# ──────────────────────────────────────────────
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
    """Compress a single log file with gzip. Returns True on success."""
    gz_path = filepath.with_suffix(filepath.suffix + ".gz")
    if gz_path.exists():
        logging.info("SKIP     Already compressed: %s", filepath.name)
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
    """Delete a log file. Returns True on success."""
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


def process_directory(directory: str, dry_run: bool) -> dict:
    """Walk *directory* and apply compress / delete rules."""
    stats = {"compressed": 0, "deleted": 0, "errors": 0, "skipped": 0}
    now = datetime.now()
    compress_threshold = now - timedelta(days=COMPRESS_AFTER_DAYS)
    delete_threshold   = now - timedelta(days=DELETE_AFTER_DAYS)

    path = Path(directory)
    if not path.exists():
        logging.warning("DIR-MISS Directory not found: %s", directory)
        return stats

    logging.info("─" * 60)
    logging.info("SCANNING %s", directory)

    for item in path.rglob("*.log"):
        if not item.is_file():
            continue

        try:
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
        except OSError as exc:
            logging.error("STAT-ERR %s | %s", item, exc)
            stats["errors"] += 1
            continue

        if mtime < delete_threshold:
            ok = delete_file(item, dry_run)
            stats["deleted"] += ok
            stats["errors"]  += not ok
        elif mtime < compress_threshold:
            ok = compress_file(item, dry_run)
            stats["compressed"] += ok
            stats["errors"]     += not ok
        else:
            stats["skipped"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Log Manager – compress & purge old logs.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate actions without modifying any files.")
    parser.add_argument("--dirs", nargs="+", default=DEFAULT_LOG_DIRS,
                        help="Directories to scan (overrides defaults).")
    args = parser.parse_args()

    if args.dry_run:
        logging.info("════ DRY-RUN MODE ENABLED – no files will be modified ════")

    totals = {"compressed": 0, "deleted": 0, "errors": 0, "skipped": 0}
    for directory in args.dirs:
        result = process_directory(directory, dry_run=args.dry_run)
        for k in totals:
            totals[k] += result[k]

    logging.info("─" * 60)
    logging.info(
        "SUMMARY  Compressed: %d | Deleted: %d | Errors: %d | Skipped: %d",
        totals["compressed"], totals["deleted"], totals["errors"], totals["skipped"],
    )


if __name__ == "__main__":
    main()
