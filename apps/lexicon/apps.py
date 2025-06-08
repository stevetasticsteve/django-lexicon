from django.apps import AppConfig


class LexiconConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.lexicon"

    def ready(self):
        # Import signals to ensure they are connected when the app is ready.
        import apps.lexicon.signals  # noqa F401
