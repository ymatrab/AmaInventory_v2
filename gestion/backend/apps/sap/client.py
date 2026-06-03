"""SAP read-only client interface (SEAM).

# SEAM: SAP integration is isolated behind this interface. The real connector
# (direct read-only DB query or SAP API call) is implemented later on the
# company network as a `SapClient` subclass. NOTHING here may write to SAP, and
# no other app may talk to SAP directly — always go through `get_sap_client()`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class SystemStockRow:
    """One row of theoretical (system) stock read from SAP.

    Item is identified by code+sku so the snapshot service can resolve it to a
    local `items.Item`. Values stay in the local zone only (CLAUDE.md §2).
    """

    warehouse_code: str
    item_code: str
    sku: str
    system_qty: Decimal
    unit_value: Decimal


class SapClient(ABC):
    """Read-only access to SAP system stock."""

    @abstractmethod
    def get_system_stock(self, campaign, warehouse) -> list[SystemStockRow]:
        """Return system-stock rows for a campaign's warehouse, read-only."""
        raise NotImplementedError
