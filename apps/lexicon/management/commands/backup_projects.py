from django.core.management.base import BaseCommand
from apps.lexicon.tasks import backup_projects

class Command(BaseCommand):
    help = "Manually trigger the backup of all lexicon projects if their version has increased"

    def handle(self, *args, **options):
        self.stdout.write("Starting project backups...")
        backup_projects()
        self.stdout.write(self.style.SUCCESS("Backup process completed."))
