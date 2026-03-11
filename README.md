# 🛠️ IT Process Automation Toolkit

A collection of Python scripts designed to automate repetitive IT support and system administration tasks. These tools focus on **maintaining system hygiene**, **optimizing storage**, and **reducing human error** in server maintenance — built to production standards for real-world deployment.

---

## 📌 Scripts Overview

| Script | Purpose |
|---|---|
| `log_manager.py` | Compresses logs older than 7 days; deletes those older than 30 days |
| `file_organizer.py` | Sorts Downloads/Temp folders into categorized subfolders |
| `disk_monitor.py` | Alerts when disk usage exceeds a configurable threshold (default 90%) |

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/it-automation-toolkit.git
cd it-automation-toolkit

# Install dependencies (only stdlib — no pip install required)
python --version   # Python 3.10+ recommended
```

### Run any script in Dry-Run mode first (recommended)

```bash
python log_manager.py   --dry-run --dirs /var/log
python file_organizer.py --dry-run --dir ~/Downloads
python disk_monitor.py  --dry-run --threshold 85
```

---

## 📂 Scripts

### 1. `log_manager.py` — Log Rotation & Cleanup

Recursively scans log directories, compresses `.log` files older than **7 days** (gzip), and permanently deletes compressed logs older than **30 days**.

```bash
# Scan default directories
python log_manager.py

# Specify custom directories
python log_manager.py --dirs /var/log /opt/myapp/logs

# Dry-run: see what would happen without doing it
python log_manager.py --dry-run --dirs /var/log
```

**Output sample:**
```
INFO     SCANNING /var/log
INFO     COMPRESS syslog.log  →  syslog.log.gz
INFO     DELETE   auth.log.gz
INFO     SUMMARY  Compressed: 4 | Deleted: 2 | Errors: 0 | Skipped: 12
```

---

### 2. `file_organizer.py` — Folder Sorter

Moves files from a messy directory into clean subfolders based on file extension:

| Subfolder | Extensions |
|---|---|
| `Images/` | `.jpg` `.png` `.gif` `.svg` `.webp` … |
| `Documents/` | `.pdf` `.docx` `.xlsx` `.txt` `.csv` … |
| `Executables/` | `.exe` `.msi` `.sh` `.deb` `.rpm` … |
| `Archives/` | `.zip` `.tar` `.gz` `.7z` `.rar` … |
| `Audio/` | `.mp3` `.wav` `.flac` `.aac` … |
| `Video/` | `.mp4` `.mkv` `.avi` `.mov` … |
| `Code/` | `.py` `.js` `.html` `.css` `.sql` … |
| `Others/` | Everything else |

```bash
# Organize Downloads folder (default)
python file_organizer.py

# Organize a custom directory
python file_organizer.py --dir /tmp/messy_folder

# Preview before moving anything
python file_organizer.py --dry-run --dir ~/Downloads
```

---

### 3. `disk_monitor.py` — Disk Usage Monitor

Checks all mounted partitions and fires an alert (log entry + OS desktop notification) if usage exceeds the threshold.

```bash
# Check all partitions with default 90% threshold
python disk_monitor.py

# Custom threshold and specific paths
python disk_monitor.py --threshold 80 --paths / /data /backup

# Dry-run: log alerts without sending notifications
python disk_monitor.py --dry-run --threshold 75
```

Generates a `disk_report.txt` after every run:
```
Disk Usage Report – 2026-03-11 14:30:00
Alert threshold: 90%
=================================================================
Mount Point                    Total       Used       Free   Use%
-----------------------------------------------------------------
/                           49.1 GiB   46.8 GiB   2.3 GiB  95.3% ⚠️ ALERT
/data                      200.0 GiB   80.0 GiB 120.0 GiB  40.0%
```

---

## 💻 Tech Stack

- **Language:** Python 3.10+
- **Libraries:** `os` · `shutil` · `gzip` · `datetime` · `pathlib` · `logging` · `argparse`
- **OS Compatibility:** Windows Server 2016+ · Linux (Ubuntu 20.04+, RHEL 8+)
- **Zero external dependencies** — uses Python standard library only

---

## 🏗️ Professional Code Standards

All scripts follow production-grade IT scripting practices:

### ✅ Structured Logging
Every action is written to `automation.log` with timestamps, log levels, and human-readable messages — ready for ingestion by log aggregators (Splunk, ELK, etc.).

```python
logging.info("COMPRESS syslog.log  →  syslog.log.gz")
logging.warning("ALERT    /var is at 95.3% capacity (2.3 GiB free).")
logging.error("PERM-ERR File in use, skipped: app.log")
```

### ✅ Dry-Run Mode
Every script supports `--dry-run`. It simulates all actions and logs what *would* happen — without touching a single file. Essential for testing in production environments.

```bash
python log_manager.py --dry-run
# INFO  [DRY-RUN] Would compress: /var/log/nginx/access.log
# INFO  [DRY-RUN] Would delete:   /var/log/old-backup.log.gz
```

### ✅ Robust Error Handling
Scripts catch `PermissionError`, `OSError`, and `shutil.Error` individually — a locked or in-use file is skipped and logged, never crashing the entire run.

```python
try:
    shutil.move(src, dest)
except PermissionError:
    logging.error("PERM-ERR File in use, skipped: %s", src.name)
except OSError as exc:
    logging.error("OS-ERR   %s | %s", src.name, exc)
```

---

## ⚙️ Automation / Scheduling

### Linux — cron

```bash
# Edit crontab
crontab -e

# Run log_manager every Sunday at 2:00 AM
0 2 * * 0   /usr/bin/python3 /opt/scripts/log_manager.py --dirs /var/log

# Check disk every hour
0 * * * *   /usr/bin/python3 /opt/scripts/disk_monitor.py --threshold 90

# Organize Downloads every weekday at 8:00 AM
0 8 * * 1-5 /usr/bin/python3 /opt/scripts/file_organizer.py --dir /home/user/Downloads
```

### Windows Server — Task Scheduler

```powershell
schtasks /create /tn "LogManager" /tr "python C:\Scripts\log_manager.py" /sc weekly /d SUN /st 02:00
schtasks /create /tn "DiskMonitor" /tr "python C:\Scripts\disk_monitor.py" /sc hourly
```

---

## 📈 Operational Impact

| Metric | Detail |
|---|---|
| **Time saved** | ~2 hours/month per server (weekly cleanup automation) |
| **Incident prevention** | Eliminates "Disk Full" errors that crash databases and services |
| **Auditability** | Full action log with timestamps for compliance and troubleshooting |
| **Safety** | Dry-run mode enables zero-risk testing in production |

---

## 📁 Project Structure

```
it-automation-toolkit/
├── log_manager.py       # Log rotation & compression
├── file_organizer.py    # Folder sorter by extension
├── disk_monitor.py      # Disk usage alert system
├── automation.log       # Generated at runtime
├── disk_report.txt      # Generated by disk_monitor.py
└── README.md
```

---

## 📄 License

MIT License — free for personal and commercial use.
