"""Phase 1: models, role groups, group-based permissions, audit log."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.accounts import groups as role_groups
from apps.accounts.audit import record_audit
from apps.accounts.models import AuditLog, FieldUser
from apps.campaigns.models import Campaign
from apps.counts.models import Count, CountLine
from apps.items.models import Item
from apps.warehouses.models import Warehouse

User = get_user_model()


@pytest.mark.django_db
def test_role_groups_exist_after_migrate():
    for name in role_groups.ALL_GROUPS:
        assert Group.objects.filter(name=name).exists()


@pytest.mark.django_db
def test_cdg_only_endpoint_enforces_group():
    client = APIClient()

    # Anonymous → rejected.
    assert client.get("/api/cdg-only/").status_code in (401, 403)

    # Authenticated but not CDG → forbidden.
    plain = User.objects.create_user("plain", password="x")
    client.force_authenticate(plain)
    assert client.get("/api/cdg-only/").status_code == 403

    # CDG member → allowed.
    cdg_user = User.objects.create_user("cdg_user", password="x")
    cdg_user.groups.add(Group.objects.get(name=role_groups.CDG))
    client.force_authenticate(cdg_user)
    resp = client.get("/api/cdg-only/")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "scope": "cdg"}


@pytest.mark.django_db
def test_whoami_returns_groups():
    user = User.objects.create_user("inv", password="x")
    user.groups.add(Group.objects.get(name=role_groups.INVENTORY_RESPONSIBLE))
    client = APIClient()
    client.force_authenticate(user)
    data = client.get("/api/whoami/").json()
    assert data["username"] == "inv"
    assert role_groups.INVENTORY_RESPONSIBLE in data["groups"]


@pytest.mark.django_db
def test_record_audit_stores_actor_and_meta():
    user = User.objects.create_user("actor", password="x")
    entry = record_audit(user, "campaign.open", "Campaign", 42, extra="info")
    assert entry.actor == user
    assert entry.entity == "Campaign"
    assert entry.entity_id == "42"
    assert entry.meta == {"extra": "info"}
    assert AuditLog.objects.count() == 1


@pytest.mark.django_db
def test_record_audit_drops_anonymous_actor():
    entry = record_audit(None, "x", "Y")
    assert entry.actor is None


@pytest.mark.django_db
def test_countline_total_units_computed_from_pack():
    item = Item.objects.create(item_code="I1", sku="I1-A", units_per_pack=12)
    wh = Warehouse.objects.create(whs_code="W1", name="W1")
    campaign = Campaign.objects.create(code="C1")
    count = Count.objects.create(campaign=campaign, warehouse=wh)
    line = CountLine.objects.create(count=count, item=item, qty_units=5, qty_packs=2)
    # 5 units + 2 packs * 12 = 29
    assert line.total_units == 29


@pytest.mark.django_db
def test_fielduser_roles():
    fu = FieldUser.objects.create(matricule="M1", full_name="Tester", role=FieldUser.Role.AGENT)
    assert fu.role == "AGENT"
