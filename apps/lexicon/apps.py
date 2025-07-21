import logging
import toml
import sys

from django.apps import AppConfig
from django.conf import settings


class LexiconConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.lexicon"

    def ready(self):
        log = logging.getLogger("lexicon")

        # Determine process type by inspecting sys.argv
        process_type = "Unknown Process"
        # sys.argv[0] can be a full path, so check for substrings
        if "gunicorn" in sys.argv[0]:
            process_type = "Gunicorn WSGI Server"
        # Celery can be invoked as `python -m celery ...` or `celery ...`
        elif "celery" in sys.argv[0] or "celery" in sys.argv:
            if "worker" in sys.argv:
                process_type = "Celery Worker"
            elif "beat" in sys.argv:
                process_type = "Celery Beat"
            else:
                process_type = "Celery Process"
        elif "manage.py" in sys.argv[0]:
            if "runserver" in sys.argv:
                process_type = "Django Development Server"
            elif "test" in sys.argv:
                process_type = "Django Test Runner"
            else:
                command = " ".join(sys.argv[1:])
                process_type = f"Django Management Command ({command})"

        # load the version from pyproject.toml
        try:
            with open("pyproject.toml", "r") as f:
                pyproject_data = toml.load(f)
                version = pyproject_data["project"]["version"]
        except FileNotFoundError:
            version = "0.0.0"  # Default if the file isn't found
        except KeyError:
            version = "0.0.0"  # Default if the 'project' or 'version' keys are missing

        log.debug(f"""
    Application v{version} started with settings:
        Process type: {process_type}
        Settings module: {settings.SETTINGS_MODULE}
        DEBUG: {settings.DEBUG}
        ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}
        SECRET_KEY: {settings.SECRET_KEY[0:4]}*****... (truncated for security)
        STATIC_ROOT: {settings.STATIC_ROOT}
        TIME_ZONE: {settings.TIME_ZONE}

        DATABASE: 
        Backend - {settings.DATABASES["default"]["ENGINE"]} 
        Host - {settings.DATABASES["default"]["HOST"]} 
        Name - {settings.DATABASES["default"]["NAME"]}

        EMAIL: 
        Backend - {settings.EMAIL_BACKEND}, 
        Host - {settings.EMAIL_HOST}, 
        Port - {settings.EMAIL_PORT}
        From address - {settings.EMAIL_HOST_USER}
        Email password - {settings.EMAIL_HOST_PASSWORD[0:4]}*****... (truncated for security)
        Admin email - {settings.ADMINS}
        
""")
