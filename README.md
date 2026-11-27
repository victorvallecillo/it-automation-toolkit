# IT Process Automation Toolkit

Three small Python scripts for log cleanup, file sorting, and disk monitoring. This is a personal project for practising routine admin tasks.

## Scripts

| Script | What it does |
|---|---|
| `log_manager.py` | Compresses `.log` files older than 7 days and deletes `.log.gz` archives older than 30 days. |
| `file_organizer.py` | Sorts files in one folder into subfolders by extension. |
| `disk_monitor.py` | Reports disk usage and can send an alert when a threshold is reached. |

## Setup

```bash
git clone https://github.com/victorvallecillo/it-automation-toolkit.git
cd it-automation-toolkit
python --version
```

Python 3.10+ is recommended. The scripts use the standard library and need no `pip install`.

## Preview before applying changes

The log manager and file organizer preview by default. Add `--apply` only after checking the planned actions. `--dry-run` is also accepted as an explicit preview option.

All scripts write `automation.log` in the current working directory. The disk monitor also creates or overwrites `disk_report.txt`, even with `--dry-run`. Its preview mode skips desktop notifications.

Try the commands against a temporary folder first:

```bash
python log_manager.py --dirs ./sample-logs
python file_organizer.py --dir ./sample-downloads
python disk_monitor.py --dry-run --threshold 85 --paths .
```

## Log Manager

The script scans the selected folders recursively. It compresses `.log` files older than seven days, then deletes `.log.gz` archives whose modification time is more than 30 days old. A newly compressed log is kept for at least 30 days after compression.

```bash
# Preview
python log_manager.py --dirs /var/log

# Apply after reviewing the preview
python log_manager.py --apply --dirs /var/log
```

## File Organizer

Only files directly inside the selected folder are considered. Files are moved into subfolders such as `Images`, `Documents`, `Archives`, and `Code`. If a destination filename already exists, a numeric suffix is added instead of overwriting it.

```bash
# Preview
python file_organizer.py --dir ~/Downloads

# Move files
python file_organizer.py --apply --dir ~/Downloads
```

## Disk Monitor

By default, the monitor checks detected partitions and uses a 90% threshold. Use `--paths` to check specific locations. Thresholds must be between 1 and 100.

```bash
python disk_monitor.py --dry-run --threshold 85 --paths / /data
```

The report is written to `disk_report.txt` in the current directory. On Linux and macOS, the script attempts to use the system notification command; Windows currently logs the alert without a desktop notification.

## Scheduling

The examples below perform real file changes. First review the same folders with the preview commands above.

### Linux — cron

```cron
# Compress old logs and remove expired archives on Sunday at 2:00 AM
0 2 * * 0 /usr/bin/python3 /opt/scripts/log_manager.py --apply --dirs /var/log

# Check disk usage each hour; desktop notifications are enabled
0 * * * * /usr/bin/python3 /opt/scripts/disk_monitor.py --threshold 90

# Sort Downloads each weekday at 8:00 AM
0 8 * * 1-5 /usr/bin/python3 /opt/scripts/file_organizer.py --apply --dir /home/user/Downloads
```

For a personal workstation, schedule the organizer only if you want files moved automatically.

## Limits

These scripts are a learning project, not a managed log-retention or monitoring service. The disk monitor reports a threshold; it does not prevent a volume from filling up. No production savings or incident-prevention results have been measured.
