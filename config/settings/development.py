"""
Development settings: SQLite, DEBUG=True, load from .env if python-dotenv is installed.
"""
import os
from pathlib import Path

from .base import *  # noqa: F401, F403

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env from project root (optional; install python-dotenv for .env support)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-not-for-production")
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1', 
    'superpatient-meridith-nonpenetrable.ngrok-free.dev',
    'overmighty-sentimental-alvina.ngrok-free.dev'
]
CSRF_TRUSTED_ORIGINS = [
    'https://superpatient-meridith-nonpenetrable.ngrok-free.dev',
    'https://overmighty-sentimental-alvina.ngrok-free.dev'
]
# SQLite for development (no DATABASE_URL)
if not os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    # PostgreSQL when DATABASE_URL is set (e.g. CI or local Postgres)
    import dj_database_url
    DATABASES = {"default": dj_database_url.config(conn_max_age=600)}

# Email configuration for development (prints to console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# For production, use these settings (configure with actual credentials):
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "smtp.gmail.com"  # or your SMTP server
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
# EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
# DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@telemedicine.com")
