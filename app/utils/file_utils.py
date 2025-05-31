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
        Only includes files matching allowed extensions and not hidden/system files.
    """
    allowed_exts = current_app.config.get("ALLOWED_UPLOAD_EXTENSIONS", set())
    file_list = []
    for dirpath, _, filenames in os.walk(root_path):
        for name in filenames:
            if name.startswith("."):
                continue  # Skip hidden/system files like .keep
            ext = os.path.splitext(name)[1].lower()
            if ext not in allowed_exts:
                continue
            rel_path = os.path.relpath(os.path.join(dirpath, name), root_path)
            abs_path = os.path.join(dirpath, name)
            size = os.path.getsize(abs_path)
            file_list.append({"name": rel_path, "size": size})
    return sorted(file_list, key=lambda x: x["name"])


# ---------------------------------------------------------------------
# End of file: app/utils/file_utils.py
# ---------------------------------------------------------------------
