#!/usr/bin/env python3
import compileall
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def main():
    paths_to_compile = [
        BASE_DIR / "app",
        BASE_DIR
    ]

    for path in paths_to_compile:
        print(f"[compile] {path}")
        compileall.compile_dir(
            path,
            force=True,
            quiet=1,
            rx = re.compile(r"translations|tests|migrations|__pycache__")

        )

if __name__ == "__main__":
    main()
