"""
disk_monitor.py
===============
Checks disk usage on all mounted partitions (or specified paths)
and logs a WARNING / triggers a desktop notification if storage
exceeds the configured threshold (default 90 %).

Usage:
    python disk_monitor.py [--dry-run] [--threshold 85] [--paths / /data]

Author: IT Automation Toolkit
"""

import os
import platform
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
ALERT_THRESHOLD_PCT = 90        # Alert when usage >= this value
LOG_FILE            = "automation.log"
REPORT_FILE         = "disk_report.txt"

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


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def bytes_to_human(n_bytes: int) -> str:
    """Convert bytes to a human-readable string (GiB / MiB / KiB)."""
    for unit in ("GiB", "MiB", "KiB"):
        divisor = {"GiB": 1 << 30, "MiB": 1 << 20, "KiB": 1 << 10}[unit]
        if n_bytes >= divisor:
            return f"{n_bytes / divisor:.1f} {unit}"
    return f"{n_bytes} B"


def send_os_notification(title: str, message: str) -> None:
    """
    Send a desktop/system notification where possible.
    Falls back to a log entry on unsupported platforms.
    """
    system = platform.system()
    try:
        if system == "Linux":
            os.system(f'notify-send "{title}" "{message}"')
        elif system == "Darwin":           # macOS
            os.system(
                f'osascript -e \'display notification "{message}" with title "{title}"\''
            )
        elif system == "Windows":
            # Requires 'plyer' or 'win10toast'; fall back to log.
            logging.warning("OS-NOTIFY Windows notification not configured. "
                            "Install 'win10toast' for desktop alerts.")
            return
        logging.info("NOTIFY   Desktop notification sent: %s", title)
    except Exception as exc:           # noqa: BLE001
        logging.error("NOTIFY-ERR Could not send notification: %s", exc)


def get_disk_partitions() -> list[str]:
    """Return mount-points / drive paths for all physical partitions."""
    partitions = []
    system = platform.system()

    if system == "Windows":
        import ctypes
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if bitmask & 1:
                partitions.append(f"{letter}:\\")
            bitmask >>= 1
    else:
        # Linux / macOS: parse /proc/mounts or use shutil fallback
        try:
            with open("/proc/mounts", "r") as fh:
                for line in fh:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].startswith("/"):
                        partitions.append(parts[1])
        except FileNotFoundError:
            partitions = ["/"]   # macOS minimal fallback

    return partitions


def check_partition(mount_point: str, threshold: int, dry_run: bool) -> dict:
    """
    Inspect a single mount-point. Returns a result dict.
    """
    result = {
        "path":       mount_point,
        "total":      0,
        "used":       0,
        "free":       0,
        "pct":        0.0,
        "alerted":    False,
        "error":      None,
    }

    try:
        usage = shutil.disk_usage(mount_point)
    except PermissionError:
        result["error"] = "Permission denied"
        logging.warning("PERM-ERR Cannot read: %s", mount_point)
        return result
    except OSError as exc:
        result["error"] = str(exc)
        logging.error("OS-ERR   %s | %s", mount_point, exc)
        return result

    result.update({
        "total": usage.total,
        "used":  usage.used,
        "free":  usage.free,
        "pct":   (usage.used / usage.total * 100) if usage.total else 0.0,
    })

    pct_str = f"{result['pct']:.1f}%"

    if result["pct"] >= threshold:
        msg = (
            f"DISK ALERT: {mount_point} is at {pct_str} capacity "
            f"({bytes_to_human(usage.free)} free of {bytes_to_human(usage.total)})."
        )
        logging.warning("ALERT    %s", msg)
        result["alerted"] = True

        if not dry_run:
            send_os_notification("⚠️ Disk Space Alert", msg)
        else:
            logging.info("[DRY-RUN] Would send notification: %s", msg)
    else:
        logging.info(
            "OK       %-30s  Used: %s  Free: %s  (%s)",
            mount_point,
            bytes_to_human(usage.used),
            bytes_to_human(usage.free),
            pct_str,
        )

    return result


def write_report(results: list[dict], threshold: int) -> None:
    """Write a plain-text disk usage report to REPORT_FILE."""
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as fh:
            fh.write(f"Disk Usage Report – {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            fh.write(f"Alert threshold: {threshold}%\n")
            fh.write("=" * 65 + "\n")
            header = f"{'Mount Point':<30} {'Total':>10} {'Used':>10} {'Free':>10} {'Use%':>6}\n"
            fh.write(header)
            fh.write("-" * 65 + "\n")
            for r in results:
                if r["error"]:
                    fh.write(f"{r['path']:<30}  ERROR: {r['error']}\n")
                    continue
                flag = " ⚠️ ALERT" if r["alerted"] else ""
                fh.write(
                    f"{r['path']:<30} "
                    f"{bytes_to_human(r['total']):>10} "
                    f"{bytes_to_human(r['used']):>10} "
                    f"{bytes_to_human(r['free']):>10} "
                    f"{r['pct']:>5.1f}%{flag}\n"
                )
        logging.info("REPORT   Written to %s", REPORT_FILE)
    except OSError as exc:
        logging.error("REPORT-ERR Could not write report: %s", exc)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Disk Monitor – alert when storage exceeds a threshold."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Log alerts without sending notifications.")
    parser.add_argument("--threshold", type=int, default=ALERT_THRESHOLD_PCT,
                        help="Usage percentage that triggers an alert (default: 90).")
    parser.add_argument("--paths", nargs="+", default=None,
                        help="Specific paths to check (default: all partitions).")
    args = parser.parse_args()

    if args.dry_run:
        logging.info("════ DRY-RUN MODE ENABLED – no notifications will be sent ════")

    paths = args.paths if args.paths else get_disk_partitions()
    logging.info("─" * 60)
    logging.info("MONITOR  Checking %d partition(s) | Threshold: %d%%",
                 len(paths), args.threshold)

    results = []
    alerts  = 0
    for mount in paths:
        r = check_partition(mount, threshold=args.threshold, dry_run=args.dry_run)
        results.append(r)
        alerts += r["alerted"]

    write_report(results, args.threshold)

    logging.info("─" * 60)
    logging.info("SUMMARY  Partitions checked: %d | Alerts triggered: %d",
                 len(results), alerts)


if __name__ == "__main__":
    main()
