"""
Django settings for the gestion (internal) backend.

Runs inside Docker on the local/VPN network only. Configuration comes from
environment variables (see gestion/.env.example). No secrets are committed.
"""

from __future__ import annotations

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present (compose also injects env_file); real secrets stay out of git.
load_dotenv(BASE_DIR.parent / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local apps
    "apps.accounts",
    "apps.warehouses",
    "apps.items",
    "apps.campaigns",
    "apps.counts",
    "apps.reconciliation",
    "apps.sap",
    "apps.sync",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL", "postgres://gestion:gestion@postgres:5432/gestion"),
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "EXCEPTION_HANDLER": "apps.accounts.exceptions.api_exception_handler",
}

# --- CORS (gestion frontend dev origin only) ---
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CORS_ALLOWED_ORIGINS", "http://localhost:5174,http://127.0.0.1:5174"
    ).split(",")
    if o.strip()
]

# --- Celery (sync poller / jobs) ---
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_TIMEZONE = TIME_ZONE

# --- Sync channel (gestion -> public; outbound only) ---
SYNC_SERVICE_TOKEN = os.environ.get("SYNC_SERVICE_TOKEN", "")
SYNC_HMAC_SECRET = os.environ.get("SYNC_HMAC_SECRET", "")
SYNC_POLL_SECONDS = int(os.environ.get("SYNC_POLL_SECONDS", "120"))
CELERY_BEAT_SCHEDULE = {
    "poll-open-campaigns": {
        "task": "apps.sync.tasks.poll_open_campaigns",
        "schedule": float(SYNC_POLL_SECONDS),
    },
}

# --- SAP / sync seams (see CLAUDE.md §2, BUILD_PLAN Phase 2/4) ---
USE_SAP_MOCK = os.environ.get("USE_SAP_MOCK", "true").lower() == "true"
# SEAM: real SAP read-only connection (unused while the mock is active).
SAP_DSN = os.environ.get("SAP_DSN", "")
SAP_DRIVER = os.environ.get("SAP_DRIVER", "")
SAP_HOST = os.environ.get("SAP_HOST", "")
SAP_PORT = os.environ.get("SAP_PORT", "")
SAP_DB = os.environ.get("SAP_DB", "")
SAP_USER = os.environ.get("SAP_USER", "")
SAP_PASSWORD = os.environ.get("SAP_PASSWORD", "")
PUBLIC_API_BASE_URL = os.environ.get("PUBLIC_API_BASE_URL", "http://localhost:3000")
