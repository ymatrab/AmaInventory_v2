"""Phase 7: gestion REST API the SPA consumes."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.accounts.groups import CDG
from apps.campaigns.models import Campaign
from apps.items.models import Item
from apps.warehouses.models import Warehouse


@pytest.fixture
def cdg_client(db):
    User = get_user_model()
    user = User.objects.create_user("cdg", password="x")
    group, _ = Group.objects.get_or_create(name=CDG)
    user.groups.add(group)
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.mark.django_db
def test_me_returns_role_flags(cdg_client):
    data = cdg_client.get("/api/auth/me/").json()
    assert data["username"] == "cdg"
    assert data["is_cdg"] is True
    assert data["is_audit"] is False


@pytest.mark.django_db
def test_campaign_crud_and_arm(cdg_client):
    warehouse = Warehouse.objects.create(whs_code="W1", name="One")
    Item.objects.create(item_code="IT-1", sku="V1")

    resp = cdg_client.post(
        "/api/campaigns/",
        {"code": "C-API", "type": "MONTHLY", "warehouse_ids": [warehouse.pk]},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    campaign_id = resp.json()["id"]

    listing = cdg_client.get("/api/campaigns/").json()
    assert any(c["code"] == "C-API" for c in listing["results"])

    armed = cdg_client.post(f"/api/campaigns/{campaign_id}/arm/")
    assert armed.status_code == 200
    assert Campaign.objects.get(pk=campaign_id).status == Campaign.Status.ARMED


@pytest.mark.django_db
def test_reconciliation_build_and_csv_download(cdg_client):
    warehouse = Warehouse.objects.create(whs_code="W1", name="One")
    Item.objects.create(item_code="IT-1", sku="V1")
    campaign = Campaign.objects.create(code="C-REC")
    from apps.reconciliation.models import SystemStock

    item = Item.objects.get(item_code="IT-1")
    SystemStock.objects.create(
        campaign=campaign, warehouse=warehouse, item=item, system_qty=10, unit_value=2
    )

    built = cdg_client.post(
        "/api/reconciliations/build/",
        {"campaign": campaign.pk, "warehouse": warehouse.pk},
        format="json",
    )
    assert built.status_code == 200
    assert len(built.json()["lines"]) == 1

    gen = cdg_client.post("/api/exports/generate/", {"campaign": campaign.pk}, format="json")
    assert gen.status_code == 200
    export_id = gen.json()["id"]

    dl = cdg_client.get(f"/api/exports/{export_id}/download/")
    assert dl.status_code == 200
    assert dl["Content-Type"] == "text/csv"


@pytest.mark.django_db
def test_unauthenticated_is_rejected():
    client = APIClient()
    assert client.get("/api/campaigns/").status_code in (401, 403)
