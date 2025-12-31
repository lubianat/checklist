import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _split_env(name, default):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-change-me")
DEBUG = os.getenv("PASSPORT_DEBUG", "False") == "True"

ALLOWED_HOSTS = _split_env(
    "ALLOWED_HOSTS",
    "checklist.toolforge.org,localhost,127.0.0.1",
)
CSRF_TRUSTED_ORIGINS = _split_env(
    "CSRF_TRUSTED_ORIGINS",
    "https://checklist.toolforge.org,http://localhost:8000",
)

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

LOCAL_APPS = [
    "accounts",
    "lists",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "passport_site.urls"

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
            ],
        },
    }
]

WSGI_APPLICATION = "passport_site.wsgi.application"
ASGI_APPLICATION = "passport_site.asgi.application"


if os.getenv("DB_ENGINE"):
    DATABASES = {
        "default": {
            "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.mysql"),
            "NAME": os.getenv("DB_NAME", "passport"),
            "USER": os.getenv("DB_USER", "passport"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", 3306),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
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

STATIC_URL = "/static/"
STATIC_ROOT = os.getenv("STATIC_ROOT", str(BASE_DIR / "static"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/auth/login/"

LOG_LEVEL = os.getenv("PASSPORT_LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        }
    },
}


OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")

OAUTH_AUTHORIZATION_SERVER = os.getenv(
    "OAUTH_AUTHORIZATION_SERVER",
    "https://www.wikidata.org",
)
OAUTH_ACCESS_TOKEN_URL = os.getenv(
    "OAUTH_ACCESS_TOKEN_URL",
    f"{OAUTH_AUTHORIZATION_SERVER}/w/rest.php/oauth2/access_token",
)
OAUTH_AUTHORIZATION_URL = os.getenv(
    "OAUTH_AUTHORIZATION_URL",
    f"{OAUTH_AUTHORIZATION_SERVER}/w/rest.php/oauth2/authorize",
)
OAUTH_PROFILE_URL = os.getenv(
    "OAUTH_PROFILE_URL",
    f"{OAUTH_AUTHORIZATION_SERVER}/w/rest.php/oauth2/resource/profile",
)

WIKIDATA_QUERY_ENDPOINT = os.getenv(
    "WIKIDATA_QUERY_ENDPOINT",
    "https://query.wikidata.org/sparql",
)
WIKIMEDIA_USER_AGENT = os.getenv("WIKIMEDIA_USER_AGENT", "checklist.toolforge.org")
