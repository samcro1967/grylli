#!/usr/bin/env python3
"""
tools/print_langs.py
Utility script to write supported language codes to a temporary file.
"""

import os
import sys

# Adjust sys.path to include the app directory so we can import local modules.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(SCRIPT_DIR, "..", "app")
sys.path.insert(0, os.path.abspath(APP_DIR))

# pylint: disable=wrong-import-position
from app.config import SUPPORTED_LANGUAGES


def main():
    """
    Write all supported language codes (keys) into 'langs.tmp' file.
    """
    output_file = "langs.tmp"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(",".join(SUPPORTED_LANGUAGES.keys()))
        print(f"✅ Wrote supported languages to {output_file}")
    except OSError as e:
        print(f"❌ Failed to write to {output_file}: {e}")


if __name__ == "__main__":
    main()
