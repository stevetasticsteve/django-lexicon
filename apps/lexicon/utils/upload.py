# These utils take bytes from a file upload and add them to the db

from django.db import IntegrityError
from .. import models


def import_dic(dic_data: bytes, project: models.LexiconProject) -> dict:
    """Import the data from a .dic file into the database.

    The data gets imported into the project specified. The dict that returns is used in
    the success url template context."""

    words = dic_data.decode("utf-8").split("\n")
    imported_words = 0
    skipped_words = 0
    for w in words:
        if not w:
            continue
        try:
            models.LexiconEntry.objects.create(tok_ples=w, project=project)
            imported_words += 1
        except IntegrityError:
            skipped_words += 1

    return {
        "words": len(words),
        "words_imported": str(imported_words),
        "words_skipped": str(skipped_words),
    }
