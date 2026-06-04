"""Phase 2: SAP read-only seam + system-stock snapshot on arming."""

import types

import pytest

from apps.campaigns.models import Campaign, CampaignWarehouse
from apps.campaigns.services import arm_campaign
from apps.items.models import Item
from apps.reconciliation.models import SystemStock
from apps.sap import get_sap_client
from apps.sap.mock import MockSapClient
from apps.sap.real import RealSapClient
from apps.warehouses.models import Warehouse


def _make_campaign_with_data():
    campaign = Campaign.objects.create(code="C-ARM")
    whs = [
        Warehouse.objects.create(whs_code="W1", name="One"),
        Warehouse.objects.create(whs_code="W2", name="Two"),
    ]
    for w in whs:
        CampaignWarehouse.objects.create(campaign=campaign, warehouse=w)
    for n in range(3):
        Item.objects.create(item_code=f"I{n}", sku=f"I{n}-A", units_per_pack=6)
    return campaign


def test_mock_is_the_default_client(settings):
    settings.USE_SAP_MOCK = True
    assert isinstance(get_sap_client(), MockSapClient)


def test_real_client_selected_when_mock_disabled(settings):
    settings.USE_SAP_MOCK = False
    assert isinstance(get_sap_client(), RealSapClient)


def test_real_client_inert_until_wired(settings):
    settings.USE_SAP_MOCK = False
    client = get_sap_client()
    warehouse = types.SimpleNamespace(whs_code="W1")
    # _connect() is a TODO seam → raises until the real connector is implemented.
    with pytest.raises(NotImplementedError):
        client.get_system_stock(campaign=None, warehouse=warehouse)


@pytest.mark.django_db
def test_arming_populates_system_stock_from_mock():
    campaign = _make_campaign_with_data()
    rows = arm_campaign(campaign)

    campaign.refresh_from_db()
    assert campaign.status == Campaign.Status.ARMED
    # 2 warehouses x 3 items
    assert rows == 6
    assert SystemStock.objects.filter(campaign=campaign).count() == 6
    # Mock values are positive.
    for stock in SystemStock.objects.filter(campaign=campaign):
        assert stock.system_qty > 0
        assert stock.unit_value > 0


@pytest.mark.django_db
def test_snapshot_is_idempotent():
    campaign = _make_campaign_with_data()
    arm_campaign(campaign)
    first = {(s.warehouse_id, s.item_id): s.system_qty for s in SystemStock.objects.all()}
    arm_campaign(campaign)
    assert SystemStock.objects.count() == 6
    second = {(s.warehouse_id, s.item_id): s.system_qty for s in SystemStock.objects.all()}
    assert first == second  # deterministic mock => stable values


@pytest.mark.django_db
def test_mock_is_deterministic_per_warehouse_item():
    campaign = _make_campaign_with_data()
    client = MockSapClient()
    warehouse = campaign.warehouses.first()
    a = client.get_system_stock(campaign, warehouse)
    b = client.get_system_stock(campaign, warehouse)
    assert a == b
