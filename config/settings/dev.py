from config.settings.base import *

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join("data", "db.sqlite3"),
    }
}

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-24#+mypq*=1v77s(37v+_$t!p7+iwdnq)$q&djz85vo$9f5sym"
ALLOWED_HOSTS = []
