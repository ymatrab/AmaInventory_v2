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

## SEAM: going live with the real connector

The real connector is **already scaffolded** — `RealSapClient` in `apps/sap/real.py`
is wired into `get_sap_client()` under the `USE_SAP_MOCK=false` branch, and stays
inert (raises `NotImplementedError`) until you fill in three things:

**① The SQL** — `apps/sap/queries/system_stock.sql`
Replace the placeholder SELECT with your read-only query. It must return columns
`warehouse_code, item_code, sku, system_qty, unit_value`, bound by `warehouse_code`.
A SAP Business One example (`OITW`/`OWHS`/`OITM`) is included in the file.

**② The connection** — `RealSapClient._connect()` in `apps/sap/real.py`
Open a **read-only** connection using your driver. Add the driver to the gestion
backend image (`requirements.txt`): e.g. `pyodbc` (SAP B1 / SQL Server) or
`hdbcli` (SAP HANA). Adjust the parameter style and `_map_row()` if your driver
returns tuples instead of dict rows.

**③ The credentials** — gestion `.env`
Set `SAP_DSN` (or `SAP_HOST/PORT/DB/USER/PASSWORD`) and flip `USE_SAP_MOCK=false`.
Keep these on the local network only; never commit real values.

Then `snapshot_system_stock()` (run on campaign arming) works unchanged — only the
client implementation differs. **Read-only: the query never mutates SAP**, and no
quantities or values from SAP ever leave the local zone.
