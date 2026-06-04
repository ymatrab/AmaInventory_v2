# 06 · SAP Connector (the seam)

[← Documentation index](../DOCUMENTATION.md)

SAP is reached through **one isolated app**: `gestion/backend/apps/sap/`. Nothing else in the
codebase talks to SAP — every caller goes through `get_sap_client()`. This is Golden Rule §4: SAP
is a **seam**, not an implementation. Today the **mock is active**; the real connector is
**already scaffolded and wired**, but stays inert until you drop in your SQL + credentials.

> The real connector is "a SQL query that reads from SAP into the gestion page with a sync logic."
> Everything below is what you fill in when you have the SAP credentials and queries.

---

## 1. The contract (stable — never changes when you go live)

```python
from apps.sap import get_sap_client, SystemStockRow

client = get_sap_client()                              # Mock today, Real when toggled
rows = client.get_system_stock(campaign, warehouse)    # -> list[SystemStockRow], READ-ONLY
```

`SystemStockRow` (dataclass, `apps/sap/client.py`):

| Field | Meaning |
|-------|---------|
| `warehouse_code` | SAP WHS code (joins to `Warehouse.whs_code`) |
| `item_code` | item code (joins to `Item.item_code`) |
| `sku` | variant (joins to `Item.sku`) |
| `system_qty` | theoretical quantity in SAP |
| `unit_value` | unit cost/value from SAP |

Whatever you do inside the real client, it must return exactly this shape. The rest of the system
(snapshot, reconciliation) is written against it and does not change.

---

## 2. The pieces

| File | Role |
|------|------|
| `apps/sap/__init__.py` | `get_sap_client()` factory. `USE_SAP_MOCK=true` → `MockSapClient`; else `RealSapClient`. **Always import via this — never import a concrete client.** |
| `apps/sap/client.py` | `SapClient` ABC + `SystemStockRow` dataclass. The contract. |
| `apps/sap/mock.py` | `MockSapClient` — deterministic, hash-seeded qty/value per (warehouse, item). Default. |
| `apps/sap/real.py` | `RealSapClient` — the scaffold you fill in. Raises `NotImplementedError` from `_connect()` until wired. |
| `apps/sap/queries/system_stock.sql` | The read-only SQL. Placeholder returns 0 rows; SAP B1 example included. |
| `apps/sap/services.py` | `snapshot_system_stock(campaign)` — calls the client per warehouse, upserts `reconciliation.SystemStock`. **Unchanged when you go live.** |
| `apps/sap/README.md` | The same go-live checklist, next to the code. |

---

## 3. How SAP data enters the system (today, with the mock)

```
campaigns.services.arm_campaign(campaign)
        │
        ▼
apps.sap.services.snapshot_system_stock(campaign)
        │   get_sap_client()  → MockSapClient (or RealSapClient when toggled)
        │   for each warehouse: client.get_system_stock(campaign, warehouse)
        ▼
reconciliation.SystemStock   (upsert per campaign/warehouse/item: system_qty, unit_value)
```

The snapshot is taken **once, at arming** — a frozen point-in-time, not a live read — so
reconciliation works against stable numbers. `snapshot_system_stock` is idempotent (re-arming
updates rows). This `SystemStock` table **never leaves the local zone**.

---

## 4. Go-live checklist (the only three things to fill in)

When you have SAP credentials and the real query, do these three. Nothing else changes.

### ① The SQL — `apps/sap/queries/system_stock.sql`
Replace the placeholder SELECT with your real **read-only** query. It must return columns named
exactly `warehouse_code, item_code, sku, system_qty, unit_value`, bound by `warehouse_code` (the
query runs once per warehouse). A SAP Business One example (`OITW`/`OWHS`/`OITM`) is in the file:

```sql
SELECT t."WhsCode" AS warehouse_code, t."ItemCode" AS item_code, t."ItemCode" AS sku,
       t."OnHand"  AS system_qty,     i."AvgPrice" AS unit_value
FROM OITW t
JOIN OWHS w ON w."WhsCode"  = t."WhsCode"
JOIN OITM i ON i."ItemCode" = t."ItemCode"
WHERE t."WhsCode" = :warehouse_code AND i."validFor" = 'Y';
```

### ② The connection — `RealSapClient._connect()` in `apps/sap/real.py`
Open a **read-only** connection with your driver, and add the driver to
`gestion/backend/requirements.txt`:

```python
# SAP B1 / SQL Server:
import pyodbc;  return pyodbc.connect(self._dsn, readonly=True)
# SAP HANA:
from hdbcli import dbapi
return dbapi.connect(address=settings.SAP_HOST, port=settings.SAP_PORT,
                     user=settings.SAP_USER, password=settings.SAP_PASSWORD)
```

Adjust `_map_row()` if your driver returns tuples instead of dict rows, and match the SQL parameter
style (`?`, `%s`, or `:name`) in `get_system_stock()`.

### ③ The credentials — gestion `.env` (never committed)
Set the `SAP_*` variables and flip the toggle:

```
USE_SAP_MOCK=false
SAP_DSN=...                       # or SAP_HOST/PORT/DB/USER/PASSWORD
SAP_DRIVER=...
```

Then `make migrate && make seed` is unaffected; the next `arm_campaign` reads real SAP. Verify with
`test_phase2.py` updated to your environment, or by arming a test campaign and inspecting
`SystemStock`.

---

## 5. Guarantees the seam enforces

- **Read-only.** The connection is opened read-only and the query is SELECT-only — the connector
  **never** mutates SAP.
- **Isolated.** No app outside `apps/sap` imports a SAP client; swapping mock↔real touches one
  factory branch.
- **Local-only.** `system_qty` and `unit_value` land in `reconciliation.SystemStock` and never
  enter any sync push payload — they do not cross the boundary (Golden Rule §2).

---

## 6. Related seam — CSV export to SAP (implemented in Phase 6)

The reverse direction (writing results back) is **also** a seam, by design: counts are **not**
written to SAP via API. Reconciliation produces a **CSV** (`reconciliation.CsvExport`) that is
imported into SAP separately (BR-09).

- **Where:** `apps/reconciliation/csv_export.py` — `DEFAULT_COLUMNS` is an ordered, human-readable
  mapping `header → dotted field path on ReconciliationLine`; `render_csv(lines, columns=None)`
  projects the lines. `apps/reconciliation/services.py::generate_csv_export()` writes the file to
  `MEDIA_ROOT/exports/` and records a `CsvExport`.
- **Default columns:** `warehouse_code, item_code, sku, system_qty, physical_qty, gap_qty,
  unit_value, gap_value, within_margin`.
- **The seam:** the exact headers/order SAP's stock-adjustment import expects are not yet known.
  Replace/extend `DEFAULT_COLUMNS` (or pass a custom `columns` mapping) when that spec arrives —
  marked `# SEAM` in `csv_export.py`. The data source does not change, only the projection.
- **Local only:** the CSV holds values and gaps; it is generated and hand-carried inside the local
  zone. It is never part of any sync payload (Golden Rule §2).
</content>
