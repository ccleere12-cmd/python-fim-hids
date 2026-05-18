# fim-hids

A Python-based File Integrity Monitoring (FIM) Host-Based Intrusion Detection System (HIDS).

`fim-hids` monitors configured directories for file changes by comparing the current state of files against a saved baseline. It detects new, deleted, and modified files, then writes the results to a structured audit log.

## Features

- Detects new files
- Detects deleted files
- Detects modified files using SHA-256 hashing
- Stores file metadata including file size and last modified time
- Detects missing or invalid baseline files
- Creates the baseline if the baseline file is missing
- Recreates the baseline if the baseline file is invalid
- Updates the baseline after detected changes
- Supports excluded file extensions
- Supports excluded directory names
- Writes structured events to an audit log
- Can be scheduled with cron
- Uses only Python standard library modules
- Designed to be cross-platform

## Technologies and Concepts Used

- Python
- JSON
- SHA-256 hashing
- Cron scheduling
- File Integrity Monitoring (FIM)
- Host-Based Intrusion Detection System (HIDS)

## Project Structure

```text
fim-hids/
├── fim_hids.py
├── config.json
├── requirements.txt
├── LICENSE
├── README.md
├── .gitignore
└── docs/
    └── fim-hids-paper.pdf
```

The following files may be generated or used at runtime:

```text
baseline.json
audit.log
cron.log
```

## How It Works

1. The program loads settings from `config.json`.
2. If the baseline file is missing, the program logs `BASELINE_MISSING` and creates a new baseline.
3. If the baseline file is invalid, the program logs `BASELINE_INVALID` and recreates the baseline.
4. The baseline stores each monitored file's path, SHA-256 hash, size, and last modified time.
5. On later runs, if a valid baseline exists, the program scans the monitored directories again.
6. The current file snapshot is compared against the baseline.
7. New, deleted, and modified files are written to the audit log.
8. If changes are detected, the baseline is updated for the next run.

The first run usually creates the baseline. File change detection begins on later runs after a valid baseline already exists.

## Configuration

The project uses a `config.json` file to define what should be monitored.

Example:

```json
{
    "monitored_directories": [
        "~/test1",
        "~/test2"
    ],
    "baseline_file": "~/fim-hids/baseline.json",
    "log_file": "~/fim-hids/audit.log",
    "excluded_directories": [
        "excluded_directory"
    ],
    "excluded_extensions": [
        ".log",
        ".tmp"
    ]
}
```

### Configuration Fields

| Field | Description |
|---|---|
| `monitored_directories` | Directories the program scans |
| `baseline_file` | Path to the JSON baseline file |
| `log_file` | Path to the audit log file |
| `excluded_directories` | Directory names to skip during scanning |
| `excluded_extensions` | File extensions to ignore |

Note: `config.json` should be placed in the same directory as `fim_hids.py`.

## Running the Program

Run the script manually:

```bash
python3 fim_hids.py
```

The program writes detected file changes to the audit log specified in `config.json`.

## Example Audit Log Output

```text
2026-04-29T21:10:01 event=BASELINE_MISSING path="/home/user/fim-hids/baseline.json"
2026-04-29T21:10:01 event=BASELINE_CREATED path="/home/user/fim-hids/baseline.json"
2026-04-29T21:15:01 event=NEW path="/home/user/fim-hids/test2/f.txt" size=120 last_modified="2026-04-29T21:14:55"
2026-04-29T21:15:01 event=DELETED path="/home/user/fim-hids/test2/e.txt" size=95 last_modified="2026-04-29T20:59:02"
2026-04-29T21:15:01 event=MODIFIED path="/home/user/fim-hids/test1/test4/b.txt" size_old=50 size_new=72 last_modified_old="2026-04-29T20:55:11" last_modified_new="2026-04-29T21:14:58"
```

If the baseline file is invalid, the audit log may include:

```text
2026-04-29T21:10:01 event=BASELINE_INVALID path="/home/user/fim-hids/baseline.json"
2026-04-29T21:10:01 event=BASELINE_RECREATED path="/home/user/fim-hids/baseline.json"
```

## Running with Cron

The script can be scheduled with cron for periodic monitoring.

Example cron entry that runs every 5 minutes:

```text
*/5 * * * * /usr/bin/python3 /home/user/fim-hids/fim_hids.py >> /home/user/fim-hids/cron.log 2>&1
```

Detected file changes are written to `audit.log`. Runtime errors and warnings can be redirected to `cron.log`.

## Requirements

This project has no external Python dependencies.

It uses only Python standard library modules:

- `os`
- `json`
- `hashlib`
- `datetime`

## Technical Paper

See the full technical design paper here:

[fim-hids-paper.pdf](docs/fim-hids-paper.pdf)

## License

This project is licensed under the MIT License.
