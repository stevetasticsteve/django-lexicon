import csv

from celery import shared_task
from django.db import IntegrityError, DataError

from apps.lexicon import models


@shared_task
def import_dic(dic_data: bytes, lang_code: str) -> None:
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
            models.LexiconEntry.objects.create(
                tok_ples=w, modified_by="importer", project=project
            )
        except IntegrityError:
            pass


@shared_task
def import_csv(csv_data: bytes, lang_code: str) -> None:
    """Import from a csv file and save into the database.

    The csv format is expected to be tok ples, english, pos, comments."""
    try:
        project = models.LexiconProject.objects.get(language_code=lang_code)
    except models.LexiconProject.DoesNotExist:
        return
    try:
        file = csv_data.decode("utf-8").split("\n")
    except UnicodeDecodeError:
        file = csv_data.decode("utf-16").split("\n")

    words = [r for r in csv.reader(file)]
    for w in words:
        try:
            models.LexiconEntry.objects.create(
                project=project,
                tok_ples=w[0],
                eng=w[1],
                pos=parse_pos(w[2]),
                comments=w[3],
                modified_by="Importer",
            )
        except IntegrityError:
            pass
        except IndexError:
            pass
        except DataError:
            pass


def parse_pos(pos: str) -> str:
    """Accepts a str representing a pos and maps it to an abbreviation.

    The abbreviation matches those expected by LexiconEntry's pos choice field."""
    pos = pos.lower()
    match pos:
        case "n":
            return "n"
        case "noun":
            return "n"
        case "adj":
            return "adj"
        case "verb":
            return "verb"
        case "v":
            return "v"
        case "adverb":
            return "adv"
        case "adv":
            return "adv"
        case "preposition":
            return "rel"
        case _:
            return "uk"
