"""Generate per-agent link + PIN for a campaign's assigned field users.

Prints the plaintext token + PIN once (hand out via printed sheet / SMS). Only
the bcrypt hash is stored. Usage:
    python manage.py generate_credentials <campaign_id>
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.campaigns.models import Campaign
from apps.campaigns.services import generate_credentials


class Command(BaseCommand):
    help = "Generate per-agent credentials (token + PIN) for an assigned campaign."

    def add_arguments(self, parser) -> None:
        parser.add_argument("campaign_id", type=int)

    def handle(self, *args, **options) -> None:
        campaign = Campaign.objects.get(pk=options["campaign_id"])
        creds = generate_credentials(campaign)
        if not creds:
            self.stdout.write(self.style.WARNING("No assignments found for this campaign."))
            return
        for c in creds:
            link = f"/c/{campaign.code}/a/{c['token']}"
            self.stdout.write(f"{c['matricule']}  PIN={c['pin']}  link={link}")
        self.stdout.write(self.style.SUCCESS(f"Generated {len(creds)} credential(s)."))
