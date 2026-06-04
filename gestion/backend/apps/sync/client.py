"""Outbound sync client: gestion -> public. The ONLY initiator of the channel.

Every call is outbound HTTPS from the local network. The public app never calls
gestion (CLAUDE.md §2). Auth per Appendix B: Bearer token + X-Timestamp +
X-Signature (HMAC-SHA256 of the raw body).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

import requests
from django.conf import settings


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


class SyncClient:
    def __init__(
        self, base_url: str | None = None, token: str | None = None, secret: str | None = None
    ):
        self.base_url = (base_url or settings.PUBLIC_API_BASE_URL).rstrip("/")
        self.token = token if token is not None else settings.SYNC_SERVICE_TOKEN
        self.secret = secret if secret is not None else settings.SYNC_HMAC_SECRET
        self.timeout = 30

    def _headers(self, body: str) -> dict[str, str]:
        signature = hmac.new(self.secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        return {
            "Authorization": f"Bearer {self.token}",
            "X-Timestamp": str(int(time.time())),
            "X-Signature": signature,
            "Content-Type": "application/json",
        }

    def _post(self, path: str, payload: Any) -> dict:
        body = json.dumps(payload, separators=(",", ":"))
        resp = requests.post(
            f"{self.base_url}{path}", data=body, headers=self._headers(body), timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()

    def _get(self, path: str, params: dict) -> dict:
        resp = requests.get(
            f"{self.base_url}{path}", params=params, headers=self._headers(""), timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()

    # --- Push (outbound) ---
    def push_campaign(self, campaign) -> dict:
        return self._post(
            "/api/sync/campaign",
            {
                "id": str(campaign.pk),
                "code": campaign.code,
                "status": campaign.status,
                "open_at": _iso(campaign.open_at),
                "close_at": _iso(campaign.close_at),
            },
        )

    def push_warehouses(self, campaign) -> dict:
        payload = [
            {
                "id": str(w.pk),
                "whs_code": w.whs_code,
                "name": w.name,
                "city": w.city,
                "campaign_id": str(campaign.pk),
            }
            for w in campaign.warehouses.all()
        ]
        return self._post("/api/sync/warehouses", payload)

    def push_items(self, campaign, items) -> dict:
        payload = [
            {
                "item_code": i.item_code,
                "sku": i.sku,
                "description": i.description,
                "color_parfum": i.color_parfum,
                "base_unit": i.base_unit,
                "units_per_pack": i.units_per_pack,
                "campaign_id": str(campaign.pk),
            }
            for i in items
        ]
        return self._post("/api/sync/items", payload)

    def push_agents(self, campaign) -> dict:
        payload = [
            {
                "agent_id": cred.field_user.matricule,
                "full_name": cred.field_user.full_name,
                "role": cred.field_user.role,
                "token": cred.token,
                "pin_hash": cred.pin_hash,
                "campaign_id": str(campaign.pk),
                "expires_at": _iso(cred.expires_at),
            }
            for cred in campaign.credentials.select_related("field_user").all()
        ]
        return self._post("/api/sync/agents", payload)

    def push_recount(self, campaign, line_uids=None, item_codes=None) -> dict:
        payload: dict[str, Any] = {"campaign_id": str(campaign.pk)}
        if line_uids:
            payload["line_uids"] = [str(u) for u in line_uids]
        if item_codes:
            payload["item_codes"] = list(item_codes)
        return self._post("/api/sync/recount", payload)

    # --- Pull (outbound) ---
    def pull_counts(self, campaign_id: str, since: str | None = None, limit: int = 200) -> dict:
        params: dict[str, Any] = {"campaign": str(campaign_id), "limit": limit}
        if since:
            params["since"] = since
        return self._get("/api/sync/counts", params)
