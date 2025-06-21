"""
# ---------------------------------------------------------------------
# file_utils.py
# app/utils/file_utils.py
# File listing utility for allowed uploads (non-hidden, filtered by extension).
# ---------------------------------------------------------------------
"""

import os

from flask import current_app


def list_available_files(root_path):
    """
    Recursively list all allowed files under the given root_path.

    Returns:
        List of dicts: { 'name': relative path, 'size': bytes }
    """
    allowed_exts = current_app.config.get("ALLOWED_UPLOAD_EXTENSIONS", set())
    file_list = []

    if not os.path.exists(root_path):
        current_app.logger.warning(f"Uploads directory missing: {root_path}")
        return []

    for dirpath, _, filenames in os.walk(root_path):
        for name in filenames:
            if name.startswith("."):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext not in allowed_exts:
                continue

            rel_path = os.path.relpath(os.path.join(dirpath, name), root_path)
            abs_path = os.path.join(dirpath, name)

            try:
                size = os.path.getsize(abs_path)
                file_list.append({"name": rel_path, "size": size})
            except Exception as e:
                current_app.logger.warning(f"Skipping unreadable file {abs_path}: {e}")

    return sorted(file_list, key=lambda x: x["name"])
