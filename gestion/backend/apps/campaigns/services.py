"""Campaign lifecycle services.

Arming a campaign transitions it to ARMED and snapshots SAP system stock into
the local SystemStock table via the SAP seam (apps.sap). Lifecycle/open-close
controls and the push to the public app are added in later phases.
"""

from __future__ import annotations

from django.db import transaction

from apps.accounts.audit import record_audit
from apps.sap.services import snapshot_system_stock

from .models import Campaign


@transaction.atomic
def arm_campaign(campaign: Campaign, actor=None) -> int:
    """Set the campaign to ARMED and snapshot system stock. Returns rows written."""
    campaign.status = Campaign.Status.ARMED
    campaign.save(update_fields=["status"])
    rows = snapshot_system_stock(campaign)
    record_audit(actor, "campaign.arm", "Campaign", campaign.pk, system_stock_rows=rows)
    return rows
