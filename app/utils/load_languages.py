"""
# ---------------------------------------------------------------------
# load_languages.py
# app/utils/load_languages.py
# Utility to safely load SUPPORTED_LANGUAGES from app.config after
# ensuring the project root is in the import path. This is used by
# scripts that are outside the core app structure but still need access
# to the app's configuration and translation setup.
# ---------------------------------------------------------------------
"""

import os
import sys

from app.utils.logging import log_error_message, log_info_message


def import_supported_languages(app_dir: str):
    """
    Adds project root to sys.path and safely imports SUPPORTED_LANGUAGES.
    Args:
        app_dir (str): Absolute path to the current app directory.
    Returns:
        dict: SUPPORTED_LANGUAGES from app.config
    """
    project_root = os.path.dirname(app_dir)
    sys.path.insert(0, project_root)

    try:
        from app.config import SUPPORTED_LANGUAGES

        log_info_message("✅ Imported SUPPORTED_LANGUAGES from app.config")
        return SUPPORTED_LANGUAGES
    except ImportError as e:
        log_error_message(f"❌ Failed to import SUPPORTED_LANGUAGES: {e}")
        sys.exit(1)
