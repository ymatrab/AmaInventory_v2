"""Manual 'Sync now': push campaign config to public, then pull counts.

A gestion UI button triggers the same flow in Phase 7. Usage:
    python manage.py sync_now <campaign_id> [--pull-only]
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.campaigns.models import Campaign
from apps.sync.client import SyncClient
from apps.sync.services import pull_counts, push_campaign_setup


class Command(BaseCommand):
    help = "Push campaign config to the public app and pull submitted counts."

    def add_arguments(self, parser) -> None:
        parser.add_argument("campaign_id", type=int)
        parser.add_argument(
            "--pull-only", action="store_true", help="Skip the push, only pull counts."
        )

    def handle(self, *args, **options) -> None:
        campaign = Campaign.objects.get(pk=options["campaign_id"])
        client = SyncClient()
        if not options["pull_only"]:
            push_campaign_setup(campaign, client)
            self.stdout.write("Pushed campaign + warehouses + items + agents.")
        pulled = pull_counts(campaign, client)
        self.stdout.write(self.style.SUCCESS(f"Pulled {pulled} count line(s)."))
