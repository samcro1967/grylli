"""
# ---------------------------------------------------------------------
# pre_translations.py
# app/pre_translations.py
# Extracts, initializes, and updates translation catalogs using Babel.
# ---------------------------------------------------------------------
"""

import os
import subprocess

import polib

from app.utils.load_languages import import_supported_languages

APP_DIR = os.path.abspath(os.path.dirname(__file__))
TRANSLATIONS_DIR = os.path.join(APP_DIR, "../app/translations")
BABEL_CFG = os.path.join(APP_DIR, "../app/babel.cfg")
POT_FILE = os.path.join(TRANSLATIONS_DIR, "messages.pot")

print(f"🔎 Working in: {APP_DIR}")

SUPPORTED_LANGUAGES = import_supported_languages(APP_DIR)

print(f"⚙️  Using babel.cfg at: {BABEL_CFG}")
print(f"⚙️  Will output messages.pot to: {POT_FILE}")

# ---------------------------------------------------------------------
# Step 1: Extract all messages from code to a .pot file
# ---------------------------------------------------------------------
subprocess.run(
    ["pybabel", "extract", "-F", BABEL_CFG, "-o", POT_FILE, os.path.join(APP_DIR, "../app")],
    check=True,
)

# ---------------------------------------------------------------------
# Step 2: For each language, initialize or update its catalog
# ---------------------------------------------------------------------
for lang in SUPPORTED_LANGUAGES:
    lang_dir = os.path.join(TRANSLATIONS_DIR, lang, "LC_MESSAGES")
    po_path = os.path.join(lang_dir, "messages.po")

    if not os.path.exists(po_path):
        print(f"🆕 Initializing new catalog for '{lang}'...")
        subprocess.run(
            ["pybabel", "init", "-i", POT_FILE, "-d", TRANSLATIONS_DIR, "-l", lang], check=True
        )
    else:
        print(f"♻️  Updating existing catalog for '{lang}'...")
        subprocess.run(
            ["pybabel", "update", "-i", POT_FILE, "-d", TRANSLATIONS_DIR, "-l", lang], check=True
        )

    # -----------------------------------------------------------------
    # Step 3: For English, sync msgstr = msgid for every entry
    # -----------------------------------------------------------------
    if lang == "en":
        print("✏️  Syncing English .po entries (msgid = msgstr)...")
        po = polib.pofile(po_path)
        for entry in po:
            if entry.msgid and (not entry.msgstr or entry.msgstr != entry.msgid):
                entry.msgstr = entry.msgid
        po.save()

print("\n✅ Pre-translation step complete. .po files are ready.")

# ---------------------------------------------------------------------
# End of file: app/pre_translations.py
# ---------------------------------------------------------------------
