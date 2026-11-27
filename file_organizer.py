"""
file_organizer.py
=================
Sorts a target folder (Downloads, Temp, etc.) by file extension,
moving files into categorized subfolders to keep workstations clean.

Usage:
    python file_organizer.py [--apply] [--dir ~/Downloads]

Author: IT Automation Toolkit
"""

import os
import shutil
import logging
import argparse
from pathlib import Path

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
DEFAULT_TARGET_DIR = str(Path.home() / "Downloads")
LOG_FILE = "automation.log"

# Extension → subfolder mapping
CATEGORY_MAP: dict[str, list[str]] = {
    "Images":      [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
                    ".webp", ".tiff", ".ico", ".heic"],
    "Documents":   [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt",
                    ".pptx", ".txt", ".csv", ".odt", ".ods", ".rtf",
                    ".md", ".log"],
    "Executables": [".exe", ".msi", ".bat", ".sh", ".cmd", ".ps1",
                    ".deb", ".rpm", ".appimage", ".dmg", ".pkg"],
    "Archives":    [".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
                    ".xz", ".iso"],
    "Audio":       [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma",
                    ".m4a"],
    "Video":       [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
                    ".webm", ".m4v"],
    "Code":        [".py", ".js", ".ts", ".html", ".css", ".java",
                    ".c", ".cpp", ".cs", ".go", ".rs", ".php",
                    ".rb", ".sql", ".json", ".xml", ".yaml", ".yml"],
    "Others":      [],   # Catch-all for unmapped extensions
}

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


def build_extension_index() -> dict[str, str]:
    """Invert CATEGORY_MAP → {'.ext': 'CategoryName'}."""
    index: dict[str, str] = {}
    for category, extensions in CATEGORY_MAP.items():
        for ext in extensions:
            index[ext.lower()] = category
    return index


def resolve_destination(dest_dir: Path, filename: str) -> Path:
    """
    If *dest_dir/filename* already exists, append a numeric suffix
    to avoid silent overwrites.
    """
    target = dest_dir / filename
    if not target.exists():
        return target

    stem   = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while target.exists():
        target = dest_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    return target


def move_file(src: Path, dest: Path, dry_run: bool) -> bool:
    """Move *src* to *dest*. Returns True on success."""
    if dry_run:
        logging.info("[DRY-RUN] Would move: %s  →  %s", src.name, dest.parent.name)
        return True

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        logging.info("MOVED    %s  →  %s/", src.name, dest.parent.name)
        return True
    except PermissionError:
        logging.error("PERM-ERR File in use, skipped: %s", src.name)
    except shutil.Error as exc:
        logging.error("MOVE-ERR %s | %s", src.name, exc)
    except OSError as exc:
        logging.error("OS-ERR   %s | %s", src.name, exc)
    return False


def organize_directory(target_dir: str, dry_run: bool) -> dict:
    """Scan *target_dir* and move files into category subfolders."""
    stats  = {"moved": 0, "errors": 0, "skipped": 0}
    ext_idx = build_extension_index()
    path    = Path(target_dir)

    if not path.exists():
        logging.error("DIR-MISS Target directory not found: %s", target_dir)
        return stats

    logging.info("─" * 60)
    logging.info("SCANNING %s", target_dir)

    # Only process files directly inside target_dir (non-recursive)
    for item in path.iterdir():
        if not item.is_file():
            stats["skipped"] += 1
            continue

        extension = item.suffix.lower()
        category  = ext_idx.get(extension, "Others")
        dest_dir  = path / category
        dest_file = resolve_destination(dest_dir, item.name)

        ok = move_file(item, dest_file, dry_run)
        stats["moved"]  += ok
        stats["errors"] += not ok

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="File Organizer – sort a folder into categorized subfolders."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true",
                      help="Move files. Preview mode is the default.")
    mode.add_argument("--dry-run", action="store_true",
                      help="Preview moves without changing files (default).")
    parser.add_argument("--dir", default=DEFAULT_TARGET_DIR,
                        help="Directory to organize (default: ~/Downloads).")
    args = parser.parse_args()

    dry_run = not args.apply
    if dry_run:
        logging.info("════ PREVIEW MODE — pass --apply to move files ════")
    else:
        logging.info("════ APPLY MODE — files will be moved ════")

    stats = organize_directory(args.dir, dry_run=dry_run)

    logging.info("─" * 60)
    action = "Would move" if dry_run else "Moved"
    logging.info(
        "SUMMARY  %s: %d | Errors: %d | Skipped (dirs/etc): %d",
        action, stats["moved"], stats["errors"], stats["skipped"],
    )


if __name__ == "__main__":
    main()
