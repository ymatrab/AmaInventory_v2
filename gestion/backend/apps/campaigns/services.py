"""Campaign lifecycle services.

Arming a campaign snapshots SAP system stock; generating credentials creates the
per-agent link + PIN that the public app authenticates against. The push to the
public app (Phase 4 sync) and the open/close lifecycle controls are elsewhere.
"""

from __future__ import annotations

import secrets

import bcrypt
from django.db import transaction
from django.utils import timezone

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


@transaction.atomic
def open_campaign(campaign: Campaign, actor=None, client=None) -> Campaign:
    """Open the counting window: status -> OPEN, stamp open_at, push status out."""
    campaign.status = Campaign.Status.OPEN
    if campaign.open_at is None:
        campaign.open_at = timezone.now()
    campaign.save(update_fields=["status", "open_at"])
    _push_status(campaign, client)
    record_audit(actor, "campaign.open", "Campaign", campaign.pk)
    return campaign


@transaction.atomic
def extend_campaign(campaign: Campaign, new_close_at, actor=None, client=None) -> Campaign:
    """Move the window's close time later (or earlier) and push it out."""
    campaign.close_at = new_close_at
    campaign.save(update_fields=["close_at"])
    _push_status(campaign, client)
    record_audit(
        actor, "campaign.extend", "Campaign", campaign.pk, close_at=new_close_at.isoformat()
    )
    return campaign


@transaction.atomic
def close_campaign(campaign: Campaign, actor=None, client=None) -> Campaign:
    """Close the campaign and expire every agent token.

    Pushing status=CLOSED is what blocks field login (the public window check
    fails); we also deactivate/expire local credentials so they cannot be reused.
    """
    now = timezone.now()
    campaign.status = Campaign.Status.CLOSED
    campaign.close_at = now
    campaign.save(update_fields=["status", "close_at"])
    campaign.credentials.update(active=False, expires_at=now)
    _push_status(campaign, client)
    record_audit(actor, "campaign.close", "Campaign", campaign.pk)
    return campaign


def _push_status(campaign: Campaign, client=None) -> None:
    """Outbound-only: push the campaign window/status to the public app."""
    from apps.sync.client import SyncClient

    client = client or SyncClient()
    client.push_campaign(campaign)
