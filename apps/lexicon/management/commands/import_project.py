# management/commands/import_project.py
from django.core.management.base import BaseCommand

from apps.lexicon.tasks import update_project_search_fields
from apps.lexicon.utils.project_import_export import import_project_from_json


class Command(BaseCommand):
    help = "Import a lexicon project from a JSON export"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)
        parser.add_argument("--overwrite", action="store_true", default=False)

    def handle(self, *args, **options):
        with open(options["file"], encoding="utf-8") as f:
            data = f.read()
        project = import_project_from_json(data, overwrite=options["overwrite"])
        self.stdout.write(self.style.SUCCESS(f"Imported project: {project}"))
        update_project_search_fields(project.language_code)
