# apps/sap — SAP read-only seam

SAP integration is **isolated behind this app** (CLAUDE.md §2, Golden Rule 4).
Nothing outside `apps/sap` talks to SAP directly — callers use `get_sap_client()`.

## Contract

```python
from apps.sap import get_sap_client, SystemStockRow

client = get_sap_client()                       # MockSapClient while USE_SAP_MOCK=true
rows = client.get_system_stock(campaign, warehouse)  # -> list[SystemStockRow], read-only
```

`SystemStockRow`: `warehouse_code, item_code, sku, system_qty, unit_value`.

The snapshot service `apps.sap.services.snapshot_system_stock(campaign)` upserts
these rows into `reconciliation.SystemStock` for every (warehouse, item) in the
campaign. It is invoked when a campaign is **armed** (`campaigns.services.arm_campaign`).

## Default: mock

`MockSapClient` returns deterministic, hash-seeded quantities/values so demos and
tests are repeatable. It is the default and the only client wired today.

## SEAM: implementing the real connector

When on the company network:

1. Add a `SapClient` subclass (e.g. `RealSapClient` in `apps/sap/real.py`) that
   performs a **read-only** SAP lookup — either a direct DB read or a SAP API call.
   Map each result to a `SystemStockRow`. **Never write to SAP.**
2. Wire it in `get_sap_client()` (`apps/sap/__init__.py`) under the
   `USE_SAP_MOCK=false` branch.
3. Configure the connection via `SAP_DSN` (or equivalent) in the gestion `.env`;
   keep it on the local network only.
4. Decide live-read vs snapshot-at-arming (we snapshot at arming for stability).

No quantities or values from SAP ever leave the local zone.
