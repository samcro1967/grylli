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


def compute_hash(path):
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def check_integrity():
    if not os.path.exists(HASH_FILE):
        raise FileNotFoundError(f"{HASH_FILE} not found")

    with open(HASH_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # List of files that are allowed to be missing in container (dev-only tools)
    optional_files = {
        "scripts/generate_screenshots.py",
        "scripts/init_db.py",
    }

def check_integrity():
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
        raise Exception("File integrity check failed:\n" + "\n".join(failures))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--silent", action="store_true", help="Suppress success output")
    args = parser.parse_args()

    try:
        check_integrity()
        if not args.silent:
            print("✅ File integrity check passed.")
        sys.exit(0)
    except Exception as e:
        print(f"{e}")
        sys.exit(1)
