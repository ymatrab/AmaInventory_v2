"""Phase 5: per-agent credential generation (token + bcrypt PIN hash)."""

import bcrypt
import pytest

from apps.accounts.models import FieldUser
from apps.campaigns.models import Assignment, Campaign
from apps.campaigns.services import generate_credentials
from apps.warehouses.models import Warehouse


@pytest.mark.django_db
def test_generate_credentials_hash_verifies_pin():
    campaign = Campaign.objects.create(code="C-CRED")
    warehouse = Warehouse.objects.create(whs_code="W1", name="One")
    field_user = FieldUser.objects.create(
        matricule="AG-9", full_name="N", role=FieldUser.Role.AGENT
    )
    Assignment.objects.create(campaign=campaign, warehouse=warehouse, field_user=field_user)

    creds = generate_credentials(campaign)
    assert len(creds) == 1
    issued = creds[0]
    assert issued["matricule"] == "AG-9"
    assert len(issued["pin"]) == 4

    cred = campaign.credentials.get()
    assert cred.token == issued["token"]
    assert cred.active
    # The stored hash verifies the issued PIN (bcrypt, interoperable with bcryptjs).
    assert bcrypt.checkpw(issued["pin"].encode(), cred.pin_hash.encode())
    assert not bcrypt.checkpw(b"0000-wrong", cred.pin_hash.encode())


@pytest.mark.django_db
def test_generate_credentials_no_assignments():
    campaign = Campaign.objects.create(code="C-CRED2")
    assert generate_credentials(campaign) == []


@pytest.mark.django_db
def test_generate_credentials_rotates_on_repeat():
    campaign = Campaign.objects.create(code="C-CRED3")
    warehouse = Warehouse.objects.create(whs_code="W2", name="Two")
    field_user = FieldUser.objects.create(
        matricule="AG-7", full_name="M", role=FieldUser.Role.AGENT
    )
    Assignment.objects.create(campaign=campaign, warehouse=warehouse, field_user=field_user)

    first = generate_credentials(campaign)[0]
    second = generate_credentials(campaign)[0]
    assert first["token"] != second["token"]  # rotated
    assert campaign.credentials.count() == 1  # still one credential per agent
