"""Sync services: push campaign config out, pull counts in (idempotently).

Pull is keyed on ``line_uid`` + ``version`` so re-polling never creates
duplicates and a failed run can be safely retried (CLAUDE.md §7).
"""

from __future__ import annotations

import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import FieldUser
from apps.counts.models import Count, CountLine
from apps.items.models import Item
from apps.warehouses.models import Warehouse

from .client import SyncClient
from .models import SyncCursor

logger = logging.getLogger(__name__)

PAGE_SIZE = 200


@transaction.atomic
def upsert_count_line(campaign, line: dict) -> bool:
    """Idempotently map one pulled public count line into gestion.

    Returns True when a row was created/updated, False when skipped (already at
    or beyond this version, or unmapped warehouse/item).
    """
    line_uid = line["line_uid"]
    incoming_version = int(line["version"])

    existing = CountLine.objects.filter(line_uid=line_uid).first()
    if existing and existing.version >= incoming_version:
        return False

    warehouse = Warehouse.objects.filter(pk=int(line["warehouse_id"])).first()
    item = Item.objects.filter(item_code=line["item_code"], sku=line["sku"]).first()
    if warehouse is None or item is None:
        logger.warning("Skipping count line %s: unmapped warehouse/item", line_uid)
        return False

    field_user = FieldUser.objects.filter(matricule=line["agent_id"]).first()
    is_recount = bool(line.get("is_recount"))

    count, _ = Count.objects.get_or_create(
        campaign=campaign, warehouse=warehouse, is_recount=is_recount
    )
    CountLine.objects.update_or_create(
        line_uid=line_uid,
        defaults={
            "count": count,
            "item": item,
            "qty_units": Decimal(str(line["qty_units"])),
            "qty_packs": Decimal(str(line["qty_packs"])),
            "counted_by": field_user,
            "flagged_for_recount": bool(line.get("flagged")),
            "version": incoming_version,
        },
    )
    count.synced_at = timezone.now()
    count.save(update_fields=["synced_at"])
    return True


def pull_counts(campaign, client: SyncClient | None = None) -> int:
    """Pull all count lines changed since the stored cursor. Returns rows written."""
    client = client or SyncClient()
    cursor_obj, _ = SyncCursor.objects.get_or_create(campaign=campaign)
    since = cursor_obj.cursor or None
    written = 0

    while True:
        data = client.pull_counts(str(campaign.pk), since=since, limit=PAGE_SIZE)
        lines = data.get("lines", [])
        if not lines:
            break
        for line in lines:
            if upsert_count_line(campaign, line):
                written += 1
        since = data.get("next_cursor") or since
        cursor_obj.cursor = since or ""
        cursor_obj.save(update_fields=["cursor", "updated_at"])
        if len(lines) < PAGE_SIZE:
            break

    return written


def push_campaign_setup(campaign, client: SyncClient | None = None, items=None) -> None:
    """Push campaign window, warehouses, item reference, and agents (outbound)."""
    client = client or SyncClient()
    if items is None:
        items = Item.objects.filter(active=True)
    client.push_campaign(campaign)
    client.push_warehouses(campaign)
    client.push_items(campaign, items)
    client.push_agents(campaign)
