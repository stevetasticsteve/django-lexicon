import os

import sentry_sdk

from config.settings.base import *  # noqa: F403
import logging

log = logging.getLogger("lexicon")

DEBUG = False
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "SECRET_KEY", "django-insecure-24#+mypq*=1v77s(37v+_$t!p7+iwdnq)$q&djz85vo$9f5sym"
)
log.debug(f"Secret key = {SECRET_KEY}")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")
log.debug(f"Allowed hosts = {ALLOWED_HOSTS}")

# email error logs
ADMINS = ["Steve", "stevetasticsteve@gmail.com"]
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.office365.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv("EMAIL_SENDER", "localhost").split(",")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_PASDWORD", "localhost").split(",")
EMAIL_USE_TLS = True
log.debug(f"Email in use {EMAIL_HOST_USER}")

# CSRF settings
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = [f"https://{site}" for site in ALLOWED_HOSTS]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True


sentry_sdk.init(
    dsn="https://b8b8bd5d2c65ec1485776d07ec1e1c90@o538547.ingest.us.sentry.io/4508379059453952",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    _experiments={
        # Set continuous_profiling_auto_start to True
        # to automatically start the profiler on when
        # possible.
        "continuous_profiling_auto_start": True,
    },
)


