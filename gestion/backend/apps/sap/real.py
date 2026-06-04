"""Real read-only SAP client (SEAM — fill in to go live).

Selected when ``USE_SAP_MOCK=false``. Reads system stock from SAP via a
read-only SQL query and maps rows to ``SystemStockRow``. Three things to fill in:

  1) `_connect()` — open a READ-ONLY connection using your driver + SAP_* settings.
  2) `apps/sap/queries/system_stock.sql` — the real SELECT query.
  3) `_map_row()` — adjust if your driver returns tuples instead of dict rows.

NEVER write to SAP. Until `_connect()` is implemented this raises
NotImplementedError, so the seam stays inert (mock remains the default).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from django.conf import settings

from .client import SapClient, SystemStockRow

QUERY_PATH = Path(__file__).resolve().parent / "queries" / "system_stock.sql"


class RealSapClient(SapClient):
    def __init__(self) -> None:
        self._dsn = getattr(settings, "SAP_DSN", "") or ""

    def _load_query(self) -> str:
        return QUERY_PATH.read_text(encoding="utf-8")

    def _connect(self):
        # TODO(SAP): open a READ-ONLY connection using SAP_* settings.
        #   SAP B1 / SQL Server:  import pyodbc; return pyodbc.connect(self._dsn, readonly=True)
        #   SAP HANA:             from hdbcli import dbapi; return dbapi.connect(
        #                             address=settings.SAP_HOST, port=settings.SAP_PORT,
        #                             user=settings.SAP_USER, password=settings.SAP_PASSWORD)
        raise NotImplementedError(
            "RealSapClient._connect is not implemented. Configure SAP_* settings "
            "and a read-only driver in apps/sap/real.py (see apps/sap/README.md)."
        )

    @staticmethod
    def _map_row(row) -> SystemStockRow:
        # TODO(SAP): if your driver returns tuples, index by position instead of key.
        return SystemStockRow(
            warehouse_code=str(row["warehouse_code"]),
            item_code=str(row["item_code"]),
            sku=str(row["sku"]),
            system_qty=Decimal(str(row["system_qty"])),
            unit_value=Decimal(str(row["unit_value"])),
        )

    def get_system_stock(self, campaign, warehouse) -> list[SystemStockRow]:
        sql = self._load_query()
        conn = self._connect()
        try:
            cursor = conn.cursor()
            # TODO(SAP): match the parameter style of your driver (?, %s, or :name).
            cursor.execute(sql, {"warehouse_code": warehouse.whs_code})
            return [self._map_row(row) for row in cursor.fetchall()]
        finally:
            conn.close()
