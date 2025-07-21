import os

from config.settings import *  # noqa: F403

SECRET_KEY = "test settings secret key"
STATIC_ROOT = None
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "lexicon_app_db",
        "USER": "django",
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "1234"),
        "HOST": "localhost",
        "PORT": 5432,
    }
}
