from django.db import models


class LexiconProject(models.Model):
    """Represents a unique language to build a lexicon for."""

    language_name = models.CharField(
        max_length=25, blank=False, null=False, verbose_name="Language name"
    )
    language_code = models.CharField(
        max_length=4,
        blank=False,
        null=False,
        unique=True,
        verbose_name="3 Digit ethnologue language code",
    )
