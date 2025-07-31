import csv
import logging

from celery import shared_task
from django.db import DataError, IntegrityError

from apps.lexicon import models

log = logging.getLogger("lexicon")


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
                text=w, modified_by="importer", project=project
            )
        except IntegrityError:
            pass


@shared_task
def import_csv(csv_data: bytes, lang_code: str) -> None:
    """Import from a csv file and save into the database.

    The csv format is expected to be text, english, pos, comments."""
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
                text=w[0],
                eng=w[1],
                pos=_parse_pos(w[2]),
                comments=w[3],
                modified_by="Importer",
            )
        except IntegrityError:
            pass
        except IndexError:
            pass
        except DataError:
            pass


def _parse_pos(pos: str) -> str:
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


@shared_task
def update_lexicon_entry_search_field(entry_pk: int) -> None:
    """Updates LexiconEntry's search field with all searchable fields for a word.

    Takes the a word's pk, finds its conjugations and variations and adds them all to a search string.
    This task is called on LexiconEntry save(), in formset.is_valid() in conjugations and on Variation save()"""
    try:
        entry = models.LexiconEntry.objects.prefetch_related(
            "variations", "conjugation_set"
        ).get(pk=entry_pk)

        # Build the search string
        search_terms = [entry.text]  # Assuming text is the main word

        for var in entry.variations.all():
            if var.included_in_search:
                search_terms.append(var.text)

        for conj in entry.conjugation_set.all():
            search_terms.append(
                conj.conjugation
            )

        new_search_field_value = " ".join(
            filter(None, search_terms)
        ).lower()  # Lowercase for case-insensitive search

        # only save if the search field changes
        if entry.search != new_search_field_value:
            entry.search = new_search_field_value
            entry.save(update_fields=["search"])  # Save only the search_field
            log.debug(f"Search for '{entry_pk}' updated to '{entry.search}'")

    except models.LexiconEntry.DoesNotExist:
        log.debug(f"LexiconEntry with pk {entry_pk} not found for search field update.")
    except Exception as e:
        log.error(f"Error updating search field for LexiconEntry {entry_pk}: {e}")
##