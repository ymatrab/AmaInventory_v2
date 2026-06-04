"""Phase 4: outbound-only sync — idempotent pull, signing, no inbound endpoint."""

import hashlib
import hmac
import uuid

import pytest
from django.urls import Resolver404, resolve

from apps.accounts.models import FieldUser
from apps.campaigns.models import Campaign, CampaignWarehouse
from apps.counts.models import CountLine
from apps.items.models import Item
from apps.sync.client import SyncClient
from apps.sync.services import pull_counts, upsert_count_line
from apps.warehouses.models import Warehouse


# --- Golden rule: gestion exposes NO inbound endpoint for the public app ---
@pytest.mark.parametrize(
    "path",
    [
        "/api/sync/counts",
        "/api/sync/campaign",
        "/api/sync/agents",
        "/api/sync/recount",
        "/sync/counts",
    ],
)
def test_gestion_has_no_inbound_sync_endpoint(path):
    with pytest.raises(Resolver404):
        resolve(path)


# --- M2M signing matches the public verifier's expectation ---
def test_sync_client_signs_body_with_hmac():
    client = SyncClient(base_url="http://public", token="tok", secret="sec")
    body = '{"a":1}'
    headers = client._headers(body)
    expected = hmac.new(b"sec", body.encode(), hashlib.sha256).hexdigest()
    assert headers["Authorization"] == "Bearer tok"
    assert headers["X-Signature"] == expected
    assert headers["X-Timestamp"].isdigit()


# --- Pull idempotency ---
def _setup_campaign_with_refs():
    campaign = Campaign.objects.create(code="C-SYNC")
    warehouse = Warehouse.objects.create(whs_code="W1", name="One")
    CampaignWarehouse.objects.create(campaign=campaign, warehouse=warehouse)
    item = Item.objects.create(item_code="ITM-1", sku="ITM-1-A", units_per_pack=6)
    FieldUser.objects.create(matricule="AG-1", full_name="A", role=FieldUser.Role.AGENT)
    return campaign, warehouse, item


def _line(warehouse, item, *, version=1, qty_units=5, qty_packs=2, flagged=False):
    return {
        "line_uid": str(uuid.uuid4()),
        "warehouse_id": str(warehouse.pk),
        "item_code": item.item_code,
        "sku": item.sku,
        "qty_units": qty_units,
        "qty_packs": qty_packs,
        "agent_id": "AG-1",
        "is_recount": False,
        "flagged": flagged,
        "version": version,
        "updated_at": "2026-06-04T00:00:00.000Z",
    }


class _FakeClient:
    """Returns one page on the first call, then nothing — simulating the public API."""

    def __init__(self, lines):
        self.lines = lines
        self.served = False

    def pull_counts(self, campaign_id, since=None, limit=200):
        if self.served:
            return {"lines": [], "next_cursor": since or ""}
        self.served = True
        last = self.lines[-1]
        return {"lines": self.lines, "next_cursor": f"{last['updated_at']}|{last['line_uid']}"}


@pytest.mark.django_db
def test_pull_counts_is_idempotent_on_repoll():
    campaign, warehouse, item = _setup_campaign_with_refs()
    lines = [_line(warehouse, item), _line(warehouse, item)]

    written = pull_counts(campaign, client=_FakeClient(lines))
    assert written == 2
    assert CountLine.objects.count() == 2

    # Re-poll the very same lines (same versions) → no duplicates, nothing written.
    rewritten = pull_counts(campaign, client=_FakeClient(lines))
    assert rewritten == 0
    assert CountLine.objects.count() == 2


@pytest.mark.django_db
def test_upsert_count_line_version_guard():
    campaign, warehouse, item = _setup_campaign_with_refs()
    line = _line(warehouse, item, version=1, qty_units=5)

    assert upsert_count_line(campaign, line) is True
    # Same version again → skipped.
    assert upsert_count_line(campaign, line) is False
    assert CountLine.objects.count() == 1

    # Higher version → updates qty + total_units, still one row.
    line_v2 = {**line, "version": 2, "qty_units": 9}
    assert upsert_count_line(campaign, line_v2) is True
    cl = CountLine.objects.get(line_uid=line["line_uid"])
    assert cl.version == 2
    assert cl.qty_units == 9
    assert cl.total_units == 9 + 2 * item.units_per_pack  # 9 + 12 = 21
    assert CountLine.objects.count() == 1


@pytest.mark.django_db
def test_upsert_skips_unmapped_item():
    campaign, warehouse, item = _setup_campaign_with_refs()
    bad = _line(warehouse, item)
    bad["sku"] = "DOES-NOT-EXIST"
    assert upsert_count_line(campaign, bad) is False
    assert CountLine.objects.count() == 0
