"""Deterministic mock SAP client (default while USE_SAP_MOCK is true).

Produces stable, plausible system quantities and unit values per
(warehouse, item) so reconciliation has data to work against without a real
SAP connection. Deterministic (hash-seeded) so tests and demos are repeatable.
"""

from __future__ import annotations

import hashlib
from decimal import Decimal

from apps.items.models import Item

from .client import SapClient, SystemStockRow


def _seed(*parts: str) -> int:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return int(digest[:8], 16)


class MockSapClient(SapClient):
    def get_system_stock(self, campaign, warehouse) -> list[SystemStockRow]:
        rows: list[SystemStockRow] = []
        for item in Item.objects.filter(active=True):
            qty = Decimal(_seed(warehouse.whs_code, item.sku) % 500 + 50)
            unit_value = Decimal(_seed(item.sku) % 9000 + 100) / Decimal(100)
            rows.append(
                SystemStockRow(
                    warehouse_code=warehouse.whs_code,
                    item_code=item.item_code,
                    sku=item.sku,
                    system_qty=qty,
                    unit_value=unit_value,
                )
            )
        return rows
