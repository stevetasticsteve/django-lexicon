import os

from django.core.management.base import BaseCommand

from apps.lexicon.utils.project_import_export import export_project_to_json


class Command(BaseCommand):
    help = "Export a lexicon project to JSON"

    def add_arguments(self, parser):
        parser.add_argument("language_code", type=str)
        parser.add_argument("--output", type=str, default=None)

    def handle(self, *args, **options):
        from apps.lexicon.models import LexiconProject

        project = LexiconProject.objects.get(language_code=options["language_code"])
        data = export_project_to_json(project.pk)
        output = options["output"] or f"{options['language_code']}_export.json"
        output = os.path.join("data", output)
        with open(output, "w", encoding="utf-8") as f:
            f.write(data)
        self.stdout.write(self.style.SUCCESS(f"Exported to {output}"))
