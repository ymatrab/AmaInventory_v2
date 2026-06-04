"""Reconciliation services (Phase 6).

CDG-facing logic, all LOCAL ZONE only (CLAUDE.md §2): join pulled physical counts
with the SAP ``SystemStock`` snapshot, compute per-item quantity and value gaps,
apply a monetary per-warehouse margin, flag items for re-count, and export a CSV
for separate SAP import.

Nothing here ever pushes stock/value/gap/margin data to the public app — the only
outbound call is ``push_recount`` (item codes / line ids), via the sync client.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.audit import record_audit
from apps.counts.models import Count, CountLine
from apps.reconciliation.csv_export import render_csv
from apps.reconciliation.models import (
    CsvExport,
    Reconciliation,
    ReconciliationLine,
    SystemStock,
)


def _physical_by_item(campaign, warehouse) -> dict[int, Decimal]:
    """Aggregate counted ``total_units`` per item for a warehouse.

    When an item has been re-counted (BR-08), the re-count value supersedes the
    original; otherwise the original count is used. The original is preserved.
    """
    lines = (
        CountLine.objects.filter(count__campaign=campaign, count__warehouse=warehouse)
        .select_related("count")
        .only("item_id", "total_units", "count__is_recount")
    )
    recounted = {line.item_id for line in lines if line.count.is_recount}

    physical: dict[int, Decimal] = {}
    for line in lines:
        # If the item was re-counted, ignore the superseded original lines.
        if line.item_id in recounted and not line.count.is_recount:
            continue
        physical[line.item_id] = physical.get(line.item_id, Decimal("0")) + line.total_units
    return physical


@transaction.atomic
def build_reconciliation(campaign, warehouse, actor=None) -> Reconciliation:
    """Compute (or refresh) the gap lines for a campaign/warehouse.

    Joins the SAP ``SystemStock`` snapshot with the aggregated physical counts and
    upserts one ``ReconciliationLine`` per item (union of both sides). Idempotent.
    """
    recon, _ = Reconciliation.objects.get_or_create(campaign=campaign, warehouse=warehouse)

    system = {
        ss.item_id: ss for ss in SystemStock.objects.filter(campaign=campaign, warehouse=warehouse)
    }
    physical = _physical_by_item(campaign, warehouse)

    for item_id in set(system) | set(physical):
        ss = system.get(item_id)
        system_qty = ss.system_qty if ss else Decimal("0")
        unit_value = ss.unit_value if ss else Decimal("0")
        physical_qty = physical.get(item_id, Decimal("0"))

        gap_qty = physical_qty - system_qty
        physical_value = physical_qty * unit_value
        system_value = system_qty * unit_value
        gap_value = physical_value - system_value

        ReconciliationLine.objects.update_or_create(
            reconciliation=recon,
            item_id=item_id,
            defaults={
                "physical_qty": physical_qty,
                "system_qty": system_qty,
                "gap_qty": gap_qty,
                "physical_value": physical_value,
                "system_value": system_value,
                "gap_value": gap_value,
            },
        )

    _apply_margin(recon)
    record_audit(
        actor,
        "reconciliation.build",
        "Reconciliation",
        recon.pk,
        warehouse=warehouse.whs_code,
        lines=recon.lines.count(),
    )
    return recon


def _apply_margin(recon: Reconciliation) -> None:
    """Flag each line ``within_margin`` when |gap_value| <= the warehouse margin.

    The margin is monetary and per-warehouse (BR-06); a zero margin means every
    non-zero value gap is out of tolerance.
    """
    margin = recon.value_margin
    for line in recon.lines.all():
        within = abs(line.gap_value) <= margin
        if within != line.within_margin:
            line.within_margin = within
            line.save(update_fields=["within_margin"])


@transaction.atomic
def set_value_margin(campaign, warehouse, margin, actor=None) -> Reconciliation:
    """Set/edit the monetary margin for a warehouse and re-flag its lines (BR-06)."""
    recon, _ = Reconciliation.objects.get_or_create(campaign=campaign, warehouse=warehouse)
    recon.value_margin = Decimal(str(margin))
    recon.set_by = actor if getattr(actor, "is_authenticated", False) else None
    recon.set_at = timezone.now()
    recon.save(update_fields=["value_margin", "set_by", "set_at"])
    _apply_margin(recon)
    record_audit(
        actor,
        "reconciliation.set_margin",
        "Reconciliation",
        recon.pk,
        warehouse=warehouse.whs_code,
        value_margin=str(recon.value_margin),
    )
    return recon


@transaction.atomic
def flag_for_recount(campaign, warehouse, item_codes, actor=None, client=None) -> Count:
    """Flag items for re-count and push the flags to the public app (BR-08).

    Creates a re-count ``Count`` as a copy of the original (preserved), marks the
    original lines flagged, moves the campaign to RECOUNT, and pushes the item
    codes outbound so agents see them in the field app.
    """
    from apps.campaigns.models import Campaign

    item_codes = list(item_codes)
    original = (
        Count.objects.filter(campaign=campaign, warehouse=warehouse, is_recount=False)
        .order_by("created_at")
        .first()
    )
    recount = Count.objects.create(
        campaign=campaign,
        warehouse=warehouse,
        is_recount=True,
        parent_count=original,
    )
    if original:
        original.lines.filter(item__item_code__in=item_codes).update(flagged_for_recount=True)

    campaign.status = Campaign.Status.RECOUNT
    campaign.save(update_fields=["status"])

    # Outbound only: push the flagged item codes to the public app.
    from apps.sync.client import SyncClient

    client = client or SyncClient()
    client.push_campaign(campaign)  # status -> RECOUNT
    if item_codes:
        client.push_recount(campaign, item_codes=item_codes)

    record_audit(
        actor,
        "reconciliation.flag_recount",
        "Count",
        recount.pk,
        warehouse=warehouse.whs_code,
        item_codes=item_codes,
    )
    return recount


@transaction.atomic
def generate_csv_export(campaign, warehouse=None, actor=None) -> CsvExport:
    """Write a reconciliation CSV for separate SAP import and record it (BR-09).

    Scoped to one warehouse, or the whole campaign when ``warehouse`` is None.
    The file lands under MEDIA_ROOT/exports/ (local zone only).
    """
    lines = (
        ReconciliationLine.objects.filter(reconciliation__campaign=campaign)
        .select_related("item", "reconciliation__warehouse")
        .order_by("reconciliation__warehouse__whs_code", "item__item_code")
    )
    if warehouse is not None:
        lines = lines.filter(reconciliation__warehouse=warehouse)

    content = render_csv(lines)

    scope = warehouse.whs_code if warehouse else "all"
    stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    rel_path = f"exports/{campaign.code}_{scope}_{stamp}.csv"
    out_path = Path(settings.MEDIA_ROOT) / rel_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")

    export = CsvExport.objects.create(campaign=campaign, warehouse=warehouse, file_ref=rel_path)
    record_audit(
        actor,
        "reconciliation.csv_export",
        "CsvExport",
        export.pk,
        warehouse=scope,
        rows=lines.count(),
    )
    return export
