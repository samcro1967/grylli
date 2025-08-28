#!/usr/bin/env python3
"""
build_wheels.py — Pre-build and cache Python wheels in a container.

- Uses python:3.11-slim-bookworm (same as build stage)
- Mounts project root and builds wheels into ./wheelhouse
- Updates sha256 manifest for reproducibility
"""

import subprocess, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQS = ROOT / "requirements.txt"
WHEELHOUSE = ROOT / "wheelhouse"
MANIFEST = WHEELHOUSE / "sha256sums.txt"

def run(cmd):
    print(f"[cmd] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def build_wheels():
    WHEELHOUSE.mkdir(exist_ok=True)

    # Run inside the matching container
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{ROOT}:/app",  # mount project root
        "-w", "/app",
        "python:3.11-slim-bookworm",
        "bash", "-c",
        (
            "apt-get update && apt-get install -y build-essential libffi-dev && "
            "pip wheel --wheel-dir=/app/wheelhouse -r /app/requirements.txt"
        ),
    ]
    run(docker_cmd)

def write_checksums():
    with MANIFEST.open("w") as mf:
        for whl in sorted(WHEELHOUSE.glob("*.whl")):
            sha256 = hashlib.sha256(whl.read_bytes()).hexdigest()
            mf.write(f"{sha256}  {whl.name}\n")
    print(f"[ok] wrote {MANIFEST}")

if __name__ == "__main__":
    build_wheels()
    write_checksums()
