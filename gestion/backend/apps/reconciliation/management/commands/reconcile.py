"""Reconcile a campaign: compute gaps per warehouse, optionally set a margin and
export the CSV. CDG workflow runner until the gestion SPA lands (Phase 7).

    python manage.py reconcile <campaign_id> [--margin 50] [--csv]
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.campaigns.models import Campaign
from apps.reconciliation.services import (
    build_reconciliation,
    generate_csv_export,
    set_value_margin,
)


class Command(BaseCommand):
    help = "Build reconciliation gaps for a campaign (all warehouses)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("campaign_id", type=int)
        parser.add_argument("--margin", type=str, default=None, help="Monetary margin per WHS.")
        parser.add_argument("--csv", action="store_true", help="Also generate a CSV export.")

    def handle(self, *args, **options) -> None:
        campaign = Campaign.objects.get(pk=options["campaign_id"])
        for warehouse in campaign.warehouses.all():
            recon = build_reconciliation(campaign, warehouse)
            if options["margin"] is not None:
                set_value_margin(campaign, warehouse, options["margin"])
                recon.refresh_from_db()
            out = sum(1 for line in recon.lines.all() if not line.within_margin)
            self.stdout.write(
                f"{warehouse.whs_code}: {recon.lines.count()} lines, "
                f"{out} out of margin (margin={recon.value_margin})"
            )
        if options["csv"]:
            export = generate_csv_export(campaign)
            self.stdout.write(self.style.SUCCESS(f"CSV: {export.file_ref}"))
        self.stdout.write(self.style.SUCCESS("Reconciliation complete."))
