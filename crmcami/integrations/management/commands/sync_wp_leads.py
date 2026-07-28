"""
Sync manual desde la CLI (mismo servicio que dispara la UI).

    python manage.py sync_wp_leads --dry-run   # cuenta, no escribe
    python manage.py sync_wp_leads             # importa (respeta throttle)
    python manage.py sync_wp_leads --force      # importa salteando throttle
"""
from django.core.management.base import BaseCommand

from integrations import services


class Command(BaseCommand):
    help = "Sincroniza leads desde WordPress (pull)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Saltea el throttle.")
        parser.add_argument("--dry-run", action="store_true", help="No escribe.")

    def handle(self, *args, **opts):
        res = services.sync(force=opts["force"], dry_run=opts["dry_run"])
        self.stdout.write(self.style.SUCCESS(str(res)))
