"""Snapshot SAP system stock into the local SystemStock table.

Called when a campaign is armed so reconciliation works against a stable
snapshot (not a moving live read). Read-only with respect to SAP.
"""

from __future__ import annotations

from django.db import transaction

from apps.items.models import Item
from apps.reconciliation.models import SystemStock

from . import get_sap_client


@transaction.atomic
def snapshot_system_stock(campaign) -> int:
    """Populate SystemStock for every (warehouse, item) in the campaign.

    Idempotent: re-arming updates existing rows. Returns the number of rows written.
    """
    client = get_sap_client()
    items_by_key = {(i.item_code, i.sku): i for i in Item.objects.all()}

    written = 0
    for warehouse in campaign.warehouses.all():
        for row in client.get_system_stock(campaign, warehouse):
            item = items_by_key.get((row.item_code, row.sku))
            if item is None:
                continue
            SystemStock.objects.update_or_create(
                campaign=campaign,
                warehouse=warehouse,
                item=item,
                defaults={"system_qty": row.system_qty, "unit_value": row.unit_value},
            )
            written += 1
    return written
