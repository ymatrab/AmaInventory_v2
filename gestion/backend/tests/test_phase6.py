"""Phase 6: reconciliation, value margins, re-count, CSV export."""

from decimal import Decimal

import pytest

from apps.campaigns.models import Campaign
from apps.campaigns.services import close_campaign, extend_campaign, open_campaign
from apps.counts.models import Count, CountLine
from apps.items.models import Item
from apps.reconciliation.csv_export import DEFAULT_COLUMNS
from apps.reconciliation.models import CsvExport, Reconciliation, SystemStock
from apps.reconciliation.services import (
    build_reconciliation,
    flag_for_recount,
    generate_csv_export,
    set_value_margin,
)
from apps.warehouses.models import Warehouse


class StubSyncClient:
    """Records outbound calls instead of hitting the network."""

    def __init__(self):
        self.calls = []

    def push_campaign(self, campaign):
        self.calls.append(("push_campaign", campaign.status))

    def push_recount(self, campaign, line_uids=None, item_codes=None):
        self.calls.append(("push_recount", list(item_codes or [])))


def _setup(code="C-RECON", system_qty=100, unit_value="2.00", physical_units=90):
    campaign = Campaign.objects.create(code=code, status=Campaign.Status.OPEN)
    warehouse = Warehouse.objects.create(whs_code=f"{code}-W", name="W")
    item = Item.objects.create(item_code="IT-1", sku="V1", units_per_pack=1)
    SystemStock.objects.create(
        campaign=campaign,
        warehouse=warehouse,
        item=item,
        system_qty=Decimal(system_qty),
        unit_value=Decimal(unit_value),
    )
    count = Count.objects.create(campaign=campaign, warehouse=warehouse, is_recount=False)
    CountLine.objects.create(count=count, item=item, qty_units=Decimal(physical_units))
    return campaign, warehouse, item


@pytest.mark.django_db
def test_build_reconciliation_computes_gap():
    campaign, warehouse, item = _setup()
    recon = build_reconciliation(campaign, warehouse)
    line = recon.lines.get(item=item)

    assert line.physical_qty == Decimal("90")
    assert line.system_qty == Decimal("100")
    assert line.gap_qty == Decimal("-10")
    # value: 90*2 - 100*2 = -20
    assert line.gap_value == Decimal("-20.00")


@pytest.mark.django_db
def test_value_margin_is_monetary_per_warehouse_and_editable():
    campaign, warehouse, item = _setup()
    build_reconciliation(campaign, warehouse)

    set_value_margin(campaign, warehouse, 25)
    recon = Reconciliation.objects.get(campaign=campaign, warehouse=warehouse)
    assert recon.value_margin == Decimal("25.00")
    assert recon.lines.get(item=item).within_margin is True  # |-20| <= 25

    # CDG tightens the margin -> the same gap is now out of tolerance.
    set_value_margin(campaign, warehouse, 10)
    assert recon.lines.get(item=item).within_margin is False  # |-20| > 10


@pytest.mark.django_db
def test_flag_for_recount_preserves_original_and_pushes():
    campaign, warehouse, item = _setup()
    original = Count.objects.get(campaign=campaign, is_recount=False)
    client = StubSyncClient()

    recount = flag_for_recount(campaign, warehouse, ["IT-1"], client=client)

    campaign.refresh_from_db()
    assert campaign.status == Campaign.Status.RECOUNT
    assert recount.is_recount is True
    assert recount.parent_count_id == original.pk  # original preserved
    assert Count.objects.filter(pk=original.pk, is_recount=False).exists()
    assert original.lines.get(item=item).flagged_for_recount is True
    assert ("push_recount", ["IT-1"]) in client.calls


@pytest.mark.django_db
def test_generate_csv_export_writes_file_and_record():
    campaign, warehouse, item = _setup()
    build_reconciliation(campaign, warehouse)

    export = generate_csv_export(campaign, warehouse)
    assert isinstance(export, CsvExport)
    assert export.file_ref.endswith(".csv")

    from pathlib import Path

    from django.conf import settings

    content = (Path(settings.MEDIA_ROOT) / export.file_ref).read_text()
    header = content.splitlines()[0]
    assert header == ",".join(DEFAULT_COLUMNS.keys())
    assert "IT-1" in content  # the item row is present


@pytest.mark.django_db
def test_close_campaign_expires_tokens_and_pushes_status():
    from apps.accounts.models import FieldUser
    from apps.campaigns.models import AgentCredential

    campaign, warehouse, item = _setup(code="C-CLOSE")
    fu = FieldUser.objects.create(matricule="AG-1", full_name="A", role=FieldUser.Role.AGENT)
    AgentCredential.objects.create(
        field_user=fu, campaign=campaign, token="tok-1", pin_hash="x", active=True
    )
    client = StubSyncClient()

    close_campaign(campaign, client=client)

    campaign.refresh_from_db()
    cred = campaign.credentials.get()
    assert campaign.status == Campaign.Status.CLOSED
    assert cred.active is False
    assert cred.expires_at is not None
    assert ("push_campaign", Campaign.Status.CLOSED) in client.calls


@pytest.mark.django_db
def test_open_and_extend_campaign_push_status():
    campaign, warehouse, item = _setup(code="C-OPEN", physical_units=100)
    client = StubSyncClient()

    open_campaign(campaign, client=client)
    campaign.refresh_from_db()
    assert campaign.status == Campaign.Status.OPEN
    assert campaign.open_at is not None

    from datetime import timedelta

    from django.utils import timezone

    new_close = timezone.now() + timedelta(days=1)
    extend_campaign(campaign, new_close, client=client)
    campaign.refresh_from_db()
    assert campaign.close_at == new_close
