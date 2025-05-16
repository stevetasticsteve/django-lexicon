import os

import sentry_sdk

from config.settings.base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "yes", "1")
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

# Celery task manager
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/0"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Pacific/Port_Moresby"
# CELERY_WORKER_LOGFILE = os.path.join(LOGGING_DIR, "scheduled_tasks.log")
# CELERY_BEAT_SCHEDULE = {
#     "update_users management command": {
#         "task": "eStatement.tasks.update_users",
#         "schedule": crontab(minute=0, hour=0),
#         "options": {
#             "expires": 15.0,
#         },
#     },
# }
