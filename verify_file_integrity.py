#!/usr/bin/env python3
"""
# ---------------------------------------------------------------------
# verify_file_integrity.py
# Project root
# Verifies SHA-256 hashes of .py, .html, and .jf files against file_hashes.sha256
# ---------------------------------------------------------------------
"""

import hashlib
import os
import sys
import argparse

HASH_FILE = "file_hashes.sha256"

class IntegrityCheckFailed(Exception):
    """
    Raised when the file integrity check detects missing or modified files
    that do not match the expected SHA-256 hashes in the manifest.
    """

def compute_hash(path):
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def check_integrity():
    """
    Verify the integrity of application files by comparing their SHA-256 hashes
    against a pre-generated manifest. Raises an exception if any discrepancies
    are found, indicating missing or modified files. Dev-only tools listed in
    `optional_files` are allowed to be absent without triggering a failure.
    
    Raises:
        FileNotFoundError: If the hash manifest file is not found.
        Exception: If any file integrity issues are detected.
    """

    if not os.path.exists(HASH_FILE):
        raise FileNotFoundError(f"{HASH_FILE} not found")

    with open(HASH_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # List of files that are allowed to be missing in container (dev-only tools)
    optional_files = {
        "scripts/generate_screenshots.py",
        "scripts/init_db.py",
    }

    failures = []
    for line in lines:
        expected_hash, rel_path = line.strip().split(maxsplit=1)
        rel_path = rel_path.strip()
        if not os.path.exists(rel_path):
            if rel_path in optional_files:
                continue  # skip optional missing file
            failures.append(f"❌ Missing file: {rel_path}")
            continue
        actual_hash = compute_hash(rel_path)
        if actual_hash != expected_hash:
            failures.append(f"❌ Modified: {rel_path}")

    if failures:
        raise IntegrityCheckFailed("File integrity check failed:\n" + "\n".join(failures))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--silent", action="store_true", help="Suppress success output")
    args = parser.parse_args()

    try:
        check_integrity()
        if not args.silent:
            print("✅ File integrity check passed.")
        sys.exit(0)
    except IntegrityCheckFailed as e:
        print(f"{e}")
        sys.exit(1)
