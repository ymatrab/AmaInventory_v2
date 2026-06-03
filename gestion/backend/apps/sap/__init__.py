"""SAP read-only seam. Use ``get_sap_client()`` — never import a concrete client."""

from __future__ import annotations

from django.conf import settings

from .client import SapClient, SystemStockRow

__all__ = ["SapClient", "SystemStockRow", "get_sap_client"]


def get_sap_client() -> SapClient:
    """Return the active SAP client.

    Defaults to the mock (``USE_SAP_MOCK=true``). When the real connector is
    implemented on the company network, wire it here behind ``USE_SAP_MOCK=false``.
    """
    if getattr(settings, "USE_SAP_MOCK", True):
        from .mock import MockSapClient

        return MockSapClient()

    # SEAM: instantiate and return the real read-only SapClient here.
    raise NotImplementedError(
        "Real SapClient not implemented. Set USE_SAP_MOCK=true or wire the "
        "real read-only connector in apps/sap (see apps/sap/README.md)."
    )
