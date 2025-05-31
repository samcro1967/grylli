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
APP_NAME = "Grylli"
APP_VERSION = "1.0.0" # Update in package.json also
GITHUB_URL = "https://github.com/samcro1967/grylli"
DEFAULT_LOCALE = "en"

# ---------------------------------------------------------------------
# FLASK RUNTIME CONFIGURATION
# ---------------------------------------------------------------------
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5069
FLASK_DEBUG = False

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
SCHEDULER_CHECKIN_INTERVAL_MINUTES = 5  # Check-ins every 1 minute
SCHEDULER_BACKUP_CRON_HOUR = 2  # 2:00 AM daily
SCHEDULER_BACKUP_CRON_MINUTE = 0

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
    "tl": "Filipino (Filipino)",
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

# ---------------------------------------------------------------------
# End of file: app/config.py
# ---------------------------------------------------------------------
