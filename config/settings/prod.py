import os
from config.settings.base import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "lexicon_app_db",
        "USER": "django",
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "1234"),
        "HOST": "db",
        "PORT": 5432,
    }
}
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", False)
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "SECRET_KEY", "django-insecure-24#+mypq*=1v77s(37v+_$t!p7+iwdnq)$q&djz85vo$9f5sym"
)
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")

# HTTPS, optional according the .env file
if os.getenv("HTTPS", "False").lower() in ("true", "yes", "1"):
    CSRF_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = [f"https://{site}" for site in ALLOWED_HOSTS]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
