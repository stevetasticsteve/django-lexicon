import os
from config.settings.base import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "lexicon_app_db",
        "USER": "django",
        "PASSWORD": "1234",
        "HOST": "db",
        "PORT": "",
    }
}

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-24#+mypq*=1v77s(37v+_$t!p7+iwdnq)$q&djz85vo$9f5sym"
ALLOWED_HOSTS = []
