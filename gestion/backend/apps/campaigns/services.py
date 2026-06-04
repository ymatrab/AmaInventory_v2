"""Campaign lifecycle services.

Arming a campaign snapshots SAP system stock; generating credentials creates the
per-agent link + PIN that the public app authenticates against. The push to the
public app (Phase 4 sync) and the open/close lifecycle controls are elsewhere.
"""

from __future__ import annotations

import secrets

import bcrypt
from django.db import transaction

from apps.accounts.audit import record_audit
from apps.sap.services import snapshot_system_stock

from .models import AgentCredential, Assignment, Campaign


@transaction.atomic
def arm_campaign(campaign: Campaign, actor=None) -> int:
    """Set the campaign to ARMED and snapshot system stock. Returns rows written."""
    campaign.status = Campaign.Status.ARMED
    campaign.save(update_fields=["status"])
    rows = snapshot_system_stock(campaign)
    record_audit(actor, "campaign.arm", "Campaign", campaign.pk, system_stock_rows=rows)
    return rows


def hash_pin(pin: str) -> str:
    """bcrypt hash (interoperable with bcryptjs on the public side)."""
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


@transaction.atomic
def generate_credentials(campaign: Campaign, actor=None) -> list[dict]:
    """Create/rotate a per-agent login (token + PIN) for each assigned field user.

    Returns the plaintext token + PIN once, for handing out (printed sheet / SMS).
    Only the bcrypt hash is stored and later pushed to the public app.
    """
    field_users = {
        a.field_user
        for a in Assignment.objects.filter(campaign=campaign).select_related("field_user")
    }
    results: list[dict] = []
    for field_user in sorted(field_users, key=lambda fu: fu.matricule):
        token = secrets.token_urlsafe(24)
        pin = f"{secrets.randbelow(10000):04d}"
        cred, _ = AgentCredential.objects.update_or_create(
            field_user=field_user,
            campaign=campaign,
            defaults={"token": token, "pin_hash": hash_pin(pin), "active": True},
        )
        record_audit(
            actor, "credential.generate", "AgentCredential", cred.pk, matricule=field_user.matricule
        )
        results.append({"matricule": field_user.matricule, "token": token, "pin": pin})
    return results
