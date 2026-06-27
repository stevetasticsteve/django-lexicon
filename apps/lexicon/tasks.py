import csv
import json
import logging
import os
from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.core.management import call_command
from django.db import DataError, IntegrityError

from apps.lexicon import models

log = logging.getLogger("lexicon")
backup_log = logging.getLogger("lexicon.backup")

BACKUP_DIR = getattr(
    settings, "BACKUP_DIR", os.path.join(settings.BASE_DIR, "data", "backups")
)


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
            "variations", "conjugations"
        ).get(pk=entry_pk)

        # Build the search string
        search_terms = [entry.text]  # Assuming text is the main word

        for var in entry.variations.all():
            if var.included_in_search:
                search_terms.append(var.text)

        for conj in entry.conjugations.all():
            search_terms.append(conj.conjugation)

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


@shared_task
def update_project_search_fields(lang_code: str) -> None:
    """Updates the search field for all entries in a project.

    This is used when the text validator changes, to update the search fields with the new validator."""
    try:
        project = models.LexiconProject.objects.get(language_code=lang_code)
        entries = models.LexiconEntry.objects.filter(project=project)
        for entry in entries:
            update_lexicon_entry_search_field(entry.pk)
    except models.LexiconProject.DoesNotExist:
        log.debug(
            f"LexiconProject with language_code {lang_code} not found for search field update."
        )
    except Exception as e:
        log.error(f"Error updating search fields for project {lang_code}: {e}")


@shared_task
def backup_projects() -> None:
    """Runs the export project management command to backup all projects as .json files.

    Each project will have its own folder in BACKUP_DIR based on its language code.
    A new backup is only created if the project's version is greater than the version
    in the latest existing backup.
    """
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    backup_log.info("Starting project backups.")

    for project in models.LexiconProject.objects.all():
        project_backup_dir = os.path.join(BACKUP_DIR, project.language_code)
        if not os.path.exists(project_backup_dir):
            os.makedirs(project_backup_dir)

        # Find latest backup
        backups = [
            f
            for f in os.listdir(project_backup_dir)
            if f.endswith(".json")
            and os.path.isfile(os.path.join(project_backup_dir, f))
        ]
        backups.sort(reverse=True)

        should_backup = True
        if backups:
            latest_backup_path = os.path.join(project_backup_dir, backups[0])
            try:
                with open(latest_backup_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    last_version = data.get("project", {}).get("version", 0)
                    if project.version <= last_version:
                        should_backup = False
                        backup_log.info(
                            f"Backup not required for {project.language_code}. "
                            f"Current version {project.version} matches or is less than latest backup version {last_version}."
                        )
            except (json.JSONDecodeError, KeyError, IOError) as e:
                log.error(f"Error reading latest backup {latest_backup_path}: {e}")
                backup_log.error(
                    f"Error reading latest backup for {project.language_code}: {e}"
                )

        if should_backup:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            filename = f"{project.language_code}_backup_{timestamp}.json"
            # We bypass the management command's default pathing because it's too restrictive
            # and use the utility directly, or we can use call_command if we ensure path is absolute.
            # The management command export_project.py uses os.path.join("data", output)
            # which is not what we want here if we want it in data/backups/<lang>/
            # Let's use call_command with an absolute path if possible,
            # but export_project command prepends "data/".

            # Since the management command is simple, let's just use the utility it uses.
            from apps.lexicon.utils.project_import_export import export_project_to_json

            try:
                data = export_project_to_json(project.pk)
                output_path = os.path.join(project_backup_dir, filename)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(data)
                log.info(f"Created backup for {project.language_code} at {output_path}")
                backup_log.info(
                    f"Created backup for {project.language_code} at {output_path}. Version: {project.version}"
                )
            except Exception as e:
                log.error(f"Failed to create backup for {project.language_code}: {e}")
                backup_log.error(
                    f"Failed to create backup for {project.language_code}: {e}"
                )

    backup_log.info("Project backups completed.")
