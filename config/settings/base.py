"""
Base settings shared across development and production.
Secrets and environment-specific options are in development.py / production.py.
"""
import os
from pathlib import Path

# Build paths relative to project root (parent of config/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: override in development/production with env
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Optional third-party: Bootstrap form styling (pip install django-crispy-forms crispy-bootstrap5)
try:
    import crispy_forms  # noqa: F401
    _CRISPY_APPS = ["crispy_forms", "crispy_bootstrap5"]
except ImportError:
    _CRISPY_APPS = []

# Optional third-party: Social authentication (pip install django-allauth)
try:
    import allauth  # noqa: F401
    _ALLAUTH_APPS = ["django.contrib.sites", "allauth", "allauth.account", "allauth.socialaccount", "allauth.socialaccount.providers.google"]
except ImportError:
    _ALLAUTH_APPS = []

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    *_CRISPY_APPS,
    *_ALLAUTH_APPS,
    # Local apps (order matters: accounts first for CustomUser)
    "accounts",
    "audit_logs",
    "appointments",
    "consultations",
    "prescriptions",
    "medical_records",
    "messaging",
    "dashboard",
]

# Django Channels - WebSocket support for real-time WebRTC signaling
INSTALLED_APPS.insert(0, "daphne")
ASGI_APPLICATION = "config.asgi.application"

# Use Redis for production, fallback to in-memory for development
import os
if os.environ.get('REDIS_URL') or os.environ.get('REDIS_HOST'):
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")],
            },
        },
    }
else:
    # Development fallback - single process only
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer"
        },
    }

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.middleware.OnlineStatusMiddleware",  # Track user online status
    "accounts.middleware.RedirectAdminToAppDashboardMiddleware",  # Redirect admins from Django admin to app dashboard
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

# Add allauth middleware if available
if _ALLAUTH_APPS:
    MIDDLEWARE.extend([
        "allauth.account.middleware.AccountMiddleware",
    ])

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Custom user model
AUTH_USER_MODEL = "accounts.CustomUser"

# Password validation (Django default; passwords hashed with PBKDF2 by default)
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media (uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login redirects
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

# Crispy forms (only used when django-crispy-forms is installed)
if _CRISPY_APPS:
    CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
    CRISPY_TEMPLATE_PACK = "bootstrap5"

# Messages framework (Bootstrap-friendly)
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# Allauth configuration
if _ALLAUTH_APPS:
    AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "allauth.account.auth_backends.AuthenticationBackend",
    ]
    
    SITE_ID = 1
    
    # Allauth settings (updated to new format)
    ACCOUNT_LOGIN_METHODS = {'email'}  # Use email for authentication
    ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']  # Required signup fields
    ACCOUNT_EMAIL_VERIFICATION = "optional"
    ACCOUNT_UNIQUE_EMAIL = True
    
    # Social account settings
    SOCIALACCOUNT_PROVIDERS = {
        "google": {
            "SCOPE": [
                "profile",
                "email",
            ],
            "AUTH_PARAMS": {
                "access_type": "online",
            },
            "APP": {
                "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
                "secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
            }
        }
    }
    
    # Login/Logout URLs
    SOCIALACCOUNT_LOGIN_ON_GET = True
