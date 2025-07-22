"""
# ---------------------------------------------------------------------
# config.py
# app/config.py
# Central Flask, database, file upload, and i18n configuration.
# ---------------------------------------------------------------------
"""

import os
from datetime import timedelta

# ---------------------------------------------------------------------
# APPLICATION METADATA
# ---------------------------------------------------------------------
APP_VERSION = "1.0.1"  # Update in package.json also
GITHUB_URL = "https://github.com/samcro1967/grylli"
DEFAULT_LOCALE = "en"
FERRET_KEY = os.environ.get("FERRET_KEY")

# ---------------------------------------------------------------------
# FLASK RUNTIME CONFIGURATION
# ---------------------------------------------------------------------
FLASK_HOST = "0.0.0.0"
FLASK_PORT = int(os.environ.get("FLASK_APP_PORT", 5069))
FLASK_DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------
# DATABASE & BACKUP STORAGE CONFIGURATION
# ---------------------------------------------------------------------
# Path to the project root (one level up from this config file, which lives in app/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Default to /data for Docker, or <project-root>/data for local dev
DATA_DIR = os.environ.get("GRYLLI_DATA_DIR", os.path.join(PROJECT_ROOT, "data"))

UPLOADS_DIR = os.environ.get("GRYLLI_UPLOADS_DIR", os.path.join(PROJECT_ROOT, "uploads"))

DATABASE_PATH = os.environ.get("GRYLLI_DB_PATH", os.path.join(DATA_DIR, "grylli.db"))

SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"

BACKUP_DIR = os.environ.get("GRYLLI_BACKUP_DIR", os.path.join(DATA_DIR, "backups"))

TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")

# ---------------------------------------------------------------------
# AUTH & SECURITY
# ---------------------------------------------------------------------
# Token expiration time for password reset and account activation (in seconds)
TOKEN_EXPIRATION_SECONDS = 600
PERMANENT_SESSION_LIFETIME = timedelta(days=7)

# ---------------------------------------------------------------------
# SCHEDULER CONFIGURATION
# ---------------------------------------------------------------------
SCHEDULER_CHECKIN_INTERVAL_MINUTES = 10  # Check-ins every 5 minutes
SCHEDULER_BACKUP_CRON_HOUR = 2  # 2:00 AM daily
SCHEDULER_BACKUP_CRON_MINUTE = 0
SCHEDULER_REMINDER_INTERVAL_MINUTES = 10
SCHEDULER_FILE_INTEGRITY_INTERVAL_MINUTES = 10
SCHEDULER_VERSION_CHECK_INTERVAL_MINUTES = 60

# ---------------------------------------------------------------------
# FILE UPLOAD VALIDATION
# ---------------------------------------------------------------------
ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".docx",
    ".xlsx",
    ".pptx",
    ".jpg",
    ".jpeg",
    ".png",
    ".csv",
    ".gif",
    ".bmp",
    ".wav",
    ".m4a",
    ".mp4",
}

ALLOWED_UPLOAD_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/bmp",
    "text/csv",
    "audio/wav",
    "audio/mp4",
}

MAX_UPLOAD_SIZE_MB = 10  # Max upload size in megabytes

# ---------------------------------------------------------------------
# INTERNATIONALIZATION (i18n)
# ---------------------------------------------------------------------
SUPPORTED_LANGUAGES = {
    "sq": "Shqip (Albanian)",
    "ar": "العربية (Arabic)",
    "az": "Azərbaycan dili (Azerbaijani)",
    "eu": "Euskara (Basque)",
    "be": "Беларуская (Belarusian)",
    "bn": "বাংলা (Bengali)",
    "bs": "Bosanski (Bosnian)",
    "my": "ဗမာစာ (Burmese)",
    "zh": "中文 (Chinese)",
    "hr": "Hrvatski (Croatian)",
    "cs": "Čeština (Czech)",
    "da": "Dansk (Danish)",
    "nl": "Nederlands (Dutch)",
    "en": "English (English)",
    "et": "Eesti (Estonian)",
    "fi": "Suomi (Finnish)",
    "fr": "Français (French)",
    "gl": "Galego (Galician)",
    "ka": "ქართული (Georgian)",
    "de": "Deutsch (German)",
    "el": "Ελληνικά (Greek)",
    "kl": "Kalaallisut (Greenlandic)",
    "gu": "ગુજરાતી (Gujarati)",
    "ha": "Hausa (Hausa)",
    "he": "עברית (Hebrew)",
    "hi": "हिन्दी (Hindi)",
    "hu": "Magyar (Hungarian)",
    "is": "Íslenska (Icelandic)",
    "ig": "Igbo (Igbo)",
    "id": "Bahasa Indonesia (Indonesian)",
    "ga": "Gaeilge (Irish)",
    "it": "Italiano (Italian)",
    "ja": "日本語 (Japanese)",
    "jv": "Basa Jawa (Javanese)",
    "ko": "한국어 (Korean)",
    "ku": "Kurdî (Kurdish (Kurmanji))",
    "lv": "Latviešu (Latvian)",
    "lt": "Lietuvių (Lithuanian)",
    "mk": "Македонски (Macedonian)",
    "mg": "Malagasy (Malagasy)",
    "ms": "Bahasa Melayu (Malay)",
    "ml": "മലയാളം (Malayalam)",
    "mt": "Malti (Maltese)",
    "mi": "Māori (Māori)",
    "no": "Norsk (Norwegian)",
    "fa": "فارسی (Persian (Farsi))",
    "pl": "Polski (Polish)",
    "pt": "Português (Portuguese)",
    "pa": "ਪੰਜਾਬੀ (Punjabi)",
    "ro": "Română (Romanian)",
    "rm": "Rumantsch (Romansh)",
    "ru": "Русский (Russian)",
    "gd": "Gàidhlig (Scottish Gaelic)",
    "sr": "Српски (Serbian)",
    "sn": "Shona (Shona)",
    "sk": "Slovenčina (Slovak)",
    "sl": "Slovenščina (Slovenian)",
    "so": "Soomaali (Somali)",
    "es": "Español (Spanish)",
    "sw": "Kiswahili (Swahili)",
    "sv": "Svenska (Swedish)",
    "ta": "தமிழ் (Tamil)",
    "te": "తెలుగు (Telugu)",
    "th": "ไทย (Thai)",
    "tr": "Türkçe (Turkish)",
    "uk": "Українська (Ukrainian)",
    "ur": "اردو (Urdu)",
    "uz": "Oʻzbekcha (Uzbek)",
    "vi": "Tiếng Việt (Vietnamese)",
    "cy": "Cymraeg (Welsh)",
    "xh": "isiXhosa (Xhosa)",
    "yo": "Yorùbá (Yoruba)",
    "zu": "isiZulu (Zulu)",
}

# config.py
LOG_FILE_PATH = os.environ.get("GRYLLI_LOG_FILE", os.path.join(PROJECT_ROOT, "data", "grylli.log"))

# Number of lines to display in the UI log viewer
UI_LOG_LINE_LIMIT = 2000

# Limit for scheduler log lines displayed in the UI
SCHEDULER_LOG_DISPLAY_LIMIT = 1000


# config.py

BACKGROUND_PATTERNS = [
    {"name": "transparent", "file": "none"},
    {"name": "bermuda-diamond", "file": "img/bermuda-diamond.svg"},
    {"name": "endless-constellation", "file": "img/endless-constellation.svg"},
    {"name": "floating-cogs", "file": "img/floating-cogs.svg"},
    {"name": "hollowed-boxes", "file": "img/hollowed-boxes.svg"},
    {"name": "overcast", "file": "img/overcast.svg"},
    {"name": "protruding-squares", "file": "img/protruding-squares.svg"},
    {"name": "wavey-fingerprint", "file": "img/wavey-fingerprint.svg"},
]

# ------------------------------------------------------------------------------
# Font Definitions
# Used for sidebar selector and font loading
# They must also be added to tailwind.config.js
# ------------------------------------------------------------------------------

AVAILABLE_FONTS = [
    {
        "key": "comic",
        "label": "Comic Neue",
        "filename": "comic-neue/files/comic-neue-latin-400-normal.woff2",
        "fallback": "cursive",
    },
    {
        "key": "gloria",
        "label": "Gloria Hallelujah",
        "filename": "gloria-hallelujah/files/gloria-hallelujah-latin-400-normal.woff2",
        "fallback": "cursive",
    },
    {
        "key": "inter",
        "label": "Inter",
        "filename": "inter/files/inter-latin-400-normal.woff2",
        "fallback": "ui-sans-serif",
    },
    {
        "key": "noto",
        "label": "Noto Sans",
        "filename": "noto-sans/files/noto-sans-latin-400-normal.woff2",
        "fallback": "sans-serif",
    },
    {
        "key": "orbitron",
        "label": "Orbitron",
        "filename": "orbitron/files/orbitron-latin-400-normal.woff2",
        "fallback": "sans-serif",
    },
    {
        "key": "pacifico",
        "label": "Pacifico",
        "filename": "pacifico/files/pacifico-latin-400-normal.woff2",
        "fallback": "cursive",
    },
    {
        "key": "patrick",
        "label": "Patrick Hand",
        "filename": "patrick-hand/files/patrick-hand-latin-400-normal.woff2",
        "fallback": "cursive",
    },
    {
        "key": "playfair",
        "label": "Playfair Display",
        "filename": "playfair-display/files/playfair-display-latin-400-normal.woff2",
        "fallback": "serif",
    },
    {
        "key": "plexmono",
        "label": "IBM Plex Mono",
        "filename": "ibm-plex-mono/files/ibm-plex-mono-latin-400-normal.woff2",
        "fallback": "monospace",
    },
    {
        "key": "rubikmono",
        "label": "Rubik Mono One",
        "filename": "rubik-mono-one/files/rubik-mono-one-latin-400-normal.woff2",
        "fallback": "monospace",
    },
    {
        "key": "sharetech",
        "label": "Share Tech Mono",
        "filename": "share-tech-mono/files/share-tech-mono-latin-400-normal.woff2",
        "fallback": "monospace",
    },
    {
        "key": "vt323",
        "label": "VT323",
        "filename": "vt323/files/vt323-latin-400-normal.woff2",
        "fallback": "monospace",
    },
    {
        "key": "rocksalt",
        "label": "Rock Salt",
        "filename": "rock-salt/files/rock-salt-latin-400-normal.woff2",
        "fallback": "cursive",
    },
    {
        "key": "audiowide",
        "label": "Audiowide",
        "filename": "audiowide/files/audiowide-latin-400-normal.woff2",
        "fallback": "sans-serif",
    },
    {
        "key": "amaticsc",
        "label": "Amatic SC",
        "filename": "amatic-sc/files/amatic-sc-latin-400-normal.woff2",
        "fallback": "cursive",
    },
    {
        "key": "schoolbell",
        "label": "Schoolbell",
        "filename": "schoolbell/files/schoolbell-latin-400-normal.woff2",
        "fallback": "cursive",
    },
    {
        "key": "lato",
        "label": "Lato",
        "filename": "lato/files/lato-latin-400-normal.woff2",
        "fallback": "sans-serif",
    },
    {
        "key": "luckiest",
        "label": "Luckiest Guy",
        "filename": "luckiest-guy/files/luckiest-guy-latin-400-normal.woff2",
        "fallback": "cursive",
    },
    {
        "key": "caveat",
        "label": "Caveat",
        "filename": "caveat/files/caveat-latin-400-normal.woff2",
        "fallback": "cursive",
    },
    {
        "key": "satisfy",
        "label": "Satisfy",
        "filename": "satisfy/files/satisfy-latin-400-normal.woff2",
        "fallback": "cursive",
    },
    {
        "key": "reenie",
        "label": "Reenie Beanie",
        "filename": "reenie-beanie/files/reenie-beanie-latin-400-normal.woff2",
        "fallback": "cursive",
    },
    {
        "key": "righteous",
        "label": "Righteous",
        "filename": "righteous/files/righteous-latin-400-normal.woff2",
        "fallback": "sans-serif",
    },
    {
        "key": "bebas",
        "label": "Bebas Neue",
        "filename": "bebas-neue/files/bebas-neue-latin-400-normal.woff2",
        "fallback": "sans-serif",
    },
    {
        "key": "baloo2",
        "label": "Baloo 2",
        "filename": "baloo-2/files/baloo-2-latin-400-normal.woff2",
        "fallback": "sans-serif",
    },
]