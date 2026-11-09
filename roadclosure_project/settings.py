import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

DJANGO_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = DJANGO_DIR.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-local-development-only")
# DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() in {"1", "true", "yes"}
DEBUG = True
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "racp.apps.RacpConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]

ROOT_URLCONF = "roadclosure_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "roadclosure_project.wsgi.application"
ASGI_APPLICATION = "roadclosure_project.asgi.application"

DATABASES = {
    "TA_VOL": {
        "ENGINE": "django_snowflake",
        "ACCOUNT": os.getenv("SNOWFLAKE_ACCOUNT", "roadclosure"),
        "NAME": os.getenv("SNOWFLAKE_DATABASE", "roadclosure"),
        "SCHEMA": os.getenv("SNOWFLAKE_SCHEMA", "roadclosure"),
        "WAREHOUSE": os.getenv("SNOWFLAKE_WAREHOUSE", "roadclosure"),
        "USER": os.getenv("SNOWFLAKE_USER", "roadclosure"),
        "PASSWORD": os.getenv("SNOWFLAKE_PASSWORD", "roadclosure"),
        "OPTIONS": {
            "role": 'PUBLIC',
            "authenticator": os.getenv("SNOWFLAKE_AUTHENTICATOR", "externalbrowser"),
            "client_session_keep_alive": True,
        },
    },
    "SW_SITE": {
        "ENGINE": "django_snowflake",
        "ACCOUNT": os.getenv("SNOWFLAKE_ACCOUNT", "roadclosure"),
        "NAME": "TDC_CURATED",
        "SCHEMA": "TSDM",
        "WAREHOUSE": os.getenv("SNOWFLAKE_WAREHOUSE", "roadclosure"),
        "USER": os.getenv("SNOWFLAKE_USER", "roadclosure"),
        "PASSWORD": os.getenv("SNOWFLAKE_PASSWORD", "roadclosure"),
        "OPTIONS": {
            "role": 'GENERAL',
            "authenticator": os.getenv("SNOWFLAKE_AUTHENTICATOR", "externalbrowser"),
            "client_session_keep_alive": True,
        },
    },
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DJANGO_DIR / "db.sqlite3",
    }
}

DATABASE_ROUTERS = ["racp.routers.SnowflakeReadOnlyRouter"]
LANGUAGE_CODE = "en-au"
TIME_ZONE = "Australia/Brisbane"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [DJANGO_DIR / "racp" / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
