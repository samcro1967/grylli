#!/usr/bin/env python3
"""
build_wheels.py — Parallelized, with fallback local build for missing wheels.

- Reads from requirements.txt (fully pinned)
- Downloads wheels for amd64 and arm64 (except those handled by docker-bake)
- Falls back to local build if remote wheel not found
- Uses 4 worker threads
- Writes sha256sums.txt
"""

import subprocess, hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent.parent
REQS = ROOT / "requirements.txt"
WHEELHOUSE = ROOT / "wheelhouse"
MANIFEST = WHEELHOUSE / "sha256sums.txt"

BUILD_DEPS = [
    "maturin==1.8.6",
    "setuptools",
    "wheel",
    "packaging",
    "pyproject_hooks",
    "pyproject_metadata",
]

PYTHON_VERSION = "3.12"
ABI = "cp312"
IMPLEMENTATION = "cp"
PLATFORMS = ["linux_x86_64", "linux_aarch64"]
MAX_WORKERS = 4

# These are built separately (via Dockerfile or bake)
EXCLUDED_FROM_WHEELHOUSE = [
    "cffi==1.16.0",
    "cryptography==45.0.3",
    "greenlet==3.2.3",
    "markupsafe==3.0.2",
    "pillow==11.3.0",
    "pyyaml==6.0.2",
]

def run(cmd):
    subprocess.run(cmd, check=True)

def ensure_qemu_registered():
    if not Path("/proc/sys/fs/binfmt_misc").exists():
        print("[warn] binfmt_misc not mounted — skipping qemu registration")
        return
    registered = Path("/proc/sys/fs/binfmt_misc/aarch64").exists()
    if not registered:
        print("[info] Registering QEMU binfmt handlers via Docker...")
        run([
            "docker", "run", "--rm", "--privileged",
            "multiarch/qemu-user-static", "--reset", "-p", "yes"
        ])
    else:
        print("[info] QEMU binfmt_misc already registered (aarch64)")

def fetch_critical_wheels():
    critical = ["cryptography==45.0.3"]
    for pkg in critical:
        for platform in PLATFORMS:
            try:
                run([
                    "pip", "download",
                    "--only-binary", ":all:",
                    "--no-deps",
                    "--dest", str(WHEELHOUSE),
                    "--platform", platform,
                    "--implementation", IMPLEMENTATION,
                    "--abi", ABI,
                    "--python-version", PYTHON_VERSION,
                    pkg,
                ])
            except subprocess.CalledProcessError as e:
                print(f"[warn] Failed to fetch critical wheel {pkg} for {platform}: {e}")

def fetch_build_deps():
    print("[info] Downloading build-time dependencies...")
    for pkg in BUILD_DEPS:
        for platform in PLATFORMS:
            try:
                run([
                    "pip", "download",
                    "--only-binary", ":all:",
                    "--no-deps",
                    "--dest", str(WHEELHOUSE),
                    "--platform", platform,
                    "--implementation", IMPLEMENTATION,
                    "--abi", ABI,
                    "--python-version", PYTHON_VERSION,
                    pkg,
                ])
            except subprocess.CalledProcessError as e:
                print(f"[warn] Failed to fetch {pkg} for {platform}: {e}")

def parse_pinned_packages():
    pkgs = []
    for line in REQS.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        pkg = line.split("==")[0].strip()
        version = line.split("==")[1].strip()
        full = f"{pkg}=={version}"
        if full not in EXCLUDED_FROM_WHEELHOUSE:
            pkgs.append(full)
    return pkgs

def download_wheel(pkg_platform):
    pkg, platform = pkg_platform
    cmd = [
        "pip", "download",
        "--only-binary", ":all:",
        "--no-deps",
        "--dest", str(WHEELHOUSE),
        "--platform", platform,
        "--implementation", IMPLEMENTATION,
        "--abi", ABI,
        "--python-version", PYTHON_VERSION,
        pkg,
    ]
    try:
        run(cmd)
        return (pkg, platform, True, "", False)
    except subprocess.CalledProcessError as e:
        return (pkg, platform, False, str(e), False)

def build_local_wheel(pkg):
    cmd = [
        "pip", "wheel",
        "--no-deps",
        "--wheel-dir", str(WHEELHOUSE),
        pkg,
    ]
    try:
        run(cmd)
        return (pkg, "local", True, "", True)
    except subprocess.CalledProcessError as e:
        return (pkg, "local", False, str(e), True)

def build_wheels():
    WHEELHOUSE.mkdir(parents=True, exist_ok=True)

    for file in WHEELHOUSE.glob("*.whl"):
        file.unlink()

    fetch_build_deps()
    fetch_critical_wheels()
    packages = parse_pinned_packages()
    targets = [
        (pkg, platform)
        for pkg in packages
        for platform in PLATFORMS
    ]
    results = []

    print(f"[info] Downloading wheels for platforms: {PLATFORMS} using {MAX_WORKERS} workers...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_wheel, t): t for t in targets}
        for future in as_completed(futures):
            results.append(future.result())

    failed_packages = sorted(set(pkg for pkg, _, ok, _, _ in results if not ok))
    if failed_packages:
        print(f"[warn] Some wheels failed remotely. Attempting local build for:")
        for pkg in failed_packages:
            print(f"  - {pkg}")
        for pkg in failed_packages:
            result = build_local_wheel(pkg)
            results.append(result)

    for tgz in WHEELHOUSE.glob("*.tar.gz"):
        print(f"[info] Removing source dist: {tgz.name}")
        tgz.unlink()

    return results

def write_checksums():
    with MANIFEST.open("w") as mf:
        for whl in sorted(WHEELHOUSE.glob("*.whl")):
            sha256 = hashlib.sha256(whl.read_bytes()).hexdigest()
            mf.write(f"{sha256}  {whl.name}")
    return len(list(WHEELHOUSE.glob("*.whl")))

def summarize(results):
    total = len(results)
    succeeded = sum(1 for r in results if r[2])
    failed = [(r[0], r[1], r[3], r[4]) for r in results if not r[2]]

    print("\n=== Build Summary ===")
    print(f"Total attempted: {total}")
    print(f"Total succeeded: {succeeded}")
    print(f"Total failed: {len(failed)}")

    if failed:
        print("\nFailures:")
        for pkg, platform, err, is_local in failed:
            tag = "local build" if is_local else "remote download"
            print(f"  - {pkg} on {platform} ({tag}): {err.splitlines()[-1] if err else 'Unknown error'}")

if __name__ == "__main__":
    ensure_qemu_registered()
    results = build_wheels()
    count = write_checksums()
    print(f"[ok] Checksums written for {count} wheels.")
    summarize(results)
