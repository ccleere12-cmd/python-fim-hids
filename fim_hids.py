#!/usr/bin/env python3

# Next things TODO (most likely in this order): 
#   - When reading the binary of a large file, reading all at once is risky. So maybe read in chunks
#   - Maybe add file permission and/or ownership tracking (see Chat #8 and notes)
#   - Maybe add summary reporting per scan (see Chat #7)
#   - Maybe add option to have log entries be sent to the user via email (and/or something else like to the terminal and/or a phone number)
#   - The project treats an empty dictionary as invalid for a baseline, but if the monitored directories are empty, then {} technically could be correct. Maybe fix this
#   - Figure out error checking (see notes; also see comment in this script for Chat's error checking example), and when to use .get(...) instead of [...]. Ask Chat to teach you how to do error checking (probably including try…catch) for this project (especially with dictionaries and nested dictionaries) without giving any answers
#   - Figure out the right folders to monitor in Linux and why. Also, if you do exclusions, figure out the right stuff to exclude/ignore in Linux
#   - Fix, clean up and add comments
#   - Figure out what the permissions on each file in your project should be

# Cron entry: */5 * * * * /usr/bin/python3 /home/cjcleere/python-fim-hids/fim_hids.py >> /home/cjcleere/python-fim-hids/cron.log 2>&1

import os
import json
import hashlib
from datetime import datetime

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIRECTORY, "config.json")

def load_config():
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    return config

def check_baseline_status(config):
    baseline_path = os.path.expanduser(config["baseline_file"])
    if not os.path.exists(baseline_path):
        return True, False  # missing baseline
    if baseline_is_invalid(config):
        return False, True  # invalid baseline 
    return False, False  # baseline exists and is valid

def baseline_is_invalid(config):
    baseline_path = os.path.expanduser(config["baseline_file"])
    if os.path.getsize(baseline_path) == 0:
        return True
    try:
        with open(baseline_path, "r") as f:
            data = json.load(f)
        if not data:  # If file just has {}
            return True
    except (json.JSONDecodeError, OSError):
        return True
    return False

def log_baseline_error(baseline_is_missing, baseline_is_invalid, config):
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with open(os.path.expanduser(config["log_file"]), "a") as f:
        if baseline_is_missing:
            f.write(f'{timestamp} event=BASELINE_MISSING path="{config["baseline_file"]}"\n')
        elif baseline_is_invalid:
            f.write(f'{timestamp} event=BASELINE_INVALID path="{config["baseline_file"]}"\n')

def scan_directories(config):
    file_metadata = {}
    for directory in config["monitored_directories"]:
        for root, dirs, files in os.walk(os.path.expanduser(directory)):  # expands ~ to user's home directory
            dirs[:] = [d for d in dirs if d not in config["excluded_directories"]]
            for file in files:
                if not file.endswith(tuple(config["excluded_extensions"])):
                    file_path = os.path.join(root, file)
                    file_metadata[file_path] = {
                        "hash": calculate_hash(file_path),
                        "last_modified": os.path.getmtime(file_path),
                        "size": os.path.getsize(file_path)
                }
    return file_metadata

def calculate_hash(file_path):
    file_hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    file_hasher.update(file_bytes)
    return file_hasher.hexdigest()

def write_baseline(config, file_metadata):
    with open(os.path.expanduser(config["baseline_file"]), "w") as f:
        json.dump(file_metadata, f, indent=4, sort_keys=True)  # Cleaner format and sorted alphabetically

def log_baseline_fix(baseline_is_missing, baseline_is_invalid, config):
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with open(os.path.expanduser(config["log_file"]), "a") as f:
        if baseline_is_missing:
            f.write(f'{timestamp} event=BASELINE_CREATED path="{config["baseline_file"]}"\n')
        elif baseline_is_invalid:
            f.write(f'{timestamp} event=BASELINE_RECREATED path="{config["baseline_file"]}"\n')

def load_baseline(config):
    with open(os.path.expanduser(config["baseline_file"]), "r") as f:
        baseline_metadata = json.load(f)
    return baseline_metadata

def compare_hashes(baseline_hashes, current_hashes, file_changes):
    for file_path in current_hashes:
        if file_path not in baseline_hashes:  
            file_changes["NEW"].append(file_path)
    for file_path, metadata in baseline_hashes.items():
        if file_path not in current_hashes:   
            file_changes["DELETED"].append(file_path)
        elif metadata.get("hash") != current_hashes.get(file_path, {}).get("hash"):  # .get(...) is safer here
            file_changes["MODIFIED"].append(file_path)

def log_changes(config, file_changes, baseline_metadata, current_metadata):
    with open(os.path.expanduser(config["log_file"]), "a") as f:
        for event_type, file_pathes in file_changes.items():
            for file_path in file_pathes:
                timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                if event_type == "NEW":
                    size = current_metadata[file_path]["size"]
                    readable_last_modified = datetime.fromtimestamp(current_metadata[file_path]["last_modified"]).strftime("%Y-%m-%dT%H:%M:%S")
                    f.write(f'{timestamp} event={event_type} path="{file_path}" size={size} last_modified="{readable_last_modified}"\n')
                elif event_type == "DELETED":
                    size = baseline_metadata[file_path]["size"]
                    readable_last_modified = datetime.fromtimestamp(baseline_metadata[file_path]["last_modified"]).strftime("%Y-%m-%dT%H:%M:%S")
                    f.write(f'{timestamp} event={event_type} path="{file_path}" size={size} last_modified="{readable_last_modified}"\n')
                elif event_type == "MODIFIED":
                    size_old = baseline_metadata[file_path]["size"]
                    size_new = current_metadata[file_path]["size"]
                    readable_last_modified_old = datetime.fromtimestamp(baseline_metadata[file_path]["last_modified"]).strftime("%Y-%m-%dT%H:%M:%S")
                    readable_last_modified_new = datetime.fromtimestamp(current_metadata[file_path]["last_modified"]).strftime("%Y-%m-%dT%H:%M:%S")
                    f.write(f'{timestamp} event={event_type} path="{file_path}" size_old={size_old} size_new={size_new} last_modified_old="{readable_last_modified_old}" last_modified_new="{readable_last_modified_new}"\n')
        
def main():

    baseline_is_missing = False
    baseline_is_invalid = False

    file_changes = {
        "NEW": [],
        "DELETED": [],
        "MODIFIED": []
    }

    config = load_config()

    baseline_is_missing, baseline_is_invalid = check_baseline_status(config)

    if baseline_is_missing or baseline_is_invalid:

        log_baseline_error(baseline_is_missing, baseline_is_invalid, config)

        # Scans MONITOR_DIRECTORY recursively, and creates a dictionary of the paths (keys) and hashes (values) of all the files that are recursively in the directory and returns it back to main to store in baseline_metadata
        baseline_metadata = scan_directories(config)

        # Opens the JSON baseline file to write to, and writes the dictionary (that was created from the scan) of file paths and hashes to the file
        write_baseline(config, baseline_metadata)

        log_baseline_fix(baseline_is_missing, baseline_is_invalid, config)
    else:
        # Loads the baseline from the JSON baseline file and returns it (as a dictionary) back to main to store in baseline_metadata
        baseline_metadata = load_baseline(config)

        # Scans MONITOR_DIRECTORY recursively, and creates a dictionary of the paths (keys) and hashes (values) of all the files that are recursively in the directory and returns it back to main to store in current_metadata
        current_metadata = scan_directories(config)

        # Compares current hashes and baseline hashes, and stores the detected changes (and the files they happened to) in the file_changes dictionary
        compare_hashes(baseline_metadata, current_metadata, file_changes)

        # Writes the detected changes (and the files they happened to) to LOG_FILE
        log_changes(config, file_changes, baseline_metadata, current_metadata)

        # If changes were detected (i.e., if any of the three values in the file_changes dictionary are not empty), update the JSON baseline file so next time the script runs it will use the correct baseline
        if file_changes["NEW"] or file_changes["DELETED"] or file_changes["MODIFIED"]:
            write_baseline(config, current_metadata)

if __name__ == "__main__":
    main()