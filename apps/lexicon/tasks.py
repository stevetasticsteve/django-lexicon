from celery import shared_task
from django.db import IntegrityError

from apps.lexicon import models


@shared_task
def import_dic(dic_data: bytes, lang_code: str) -> dict:
    """Import the data from a .dic file into the database.

    The data gets imported into the project specified. The dict that returns is used in
    the success url template context."""
    try:
        project = models.LexiconProject.objects.get(language_code=lang_code)
    except models.LexiconProject.DoesNotExist:
        return
    try:
        words = dic_data.decode("utf-8").split("\n")
    except UnicodeDecodeError:
        words = dic_data.decode("utf-16").split("\n")
    for w in words:
        if not w:
            continue
        try:
            models.LexiconEntry.objects.create(tok_ples=w, project=project)
        except IntegrityError:
            pass
