"""CSV export for separate SAP import (Phase 6, BR-09).

The reconciliation result is exported as a CSV that is imported into SAP through a
**separate** process — counts are never written back to SAP over an API (Golden
Rule §4 / §1). The column mapping is configurable: ``DEFAULT_COLUMNS`` is a
documented, human-readable default; the real SAP import layout is wired later.

# SEAM: real SAP import column mapping. Replace/extend ``DEFAULT_COLUMNS`` (or pass
# a custom ``columns`` mapping) with the exact headers + field order SAP's stock
# adjustment / count import expects once that spec is known. The data source
# (ReconciliationLine) does not change — only the projection below.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable

from apps.reconciliation.models import ReconciliationLine

# Ordered mapping: output CSV header -> callable(line) producing the cell value.
# Keep value/gap columns out of any payload that crosses the boundary — this file
# is local-zone only and its output is hand-carried into SAP.
DEFAULT_COLUMNS: dict[str, str] = {
    "warehouse_code": "reconciliation.warehouse.whs_code",
    "item_code": "item.item_code",
    "sku": "item.sku",
    "system_qty": "system_qty",
    "physical_qty": "physical_qty",
    "gap_qty": "gap_qty",
    "unit_value": "unit_value",
    "gap_value": "gap_value",
    "within_margin": "within_margin",
}


def _resolve(line: ReconciliationLine, dotted: str):
    """Resolve a dotted attribute path (e.g. ``reconciliation.warehouse.whs_code``)."""
    if dotted == "unit_value":
        # unit_value lives on the SAP snapshot, not the line; derive it safely.
        return line.system_value / line.system_qty if line.system_qty else 0
    value = line
    for part in dotted.split("."):
        value = getattr(value, part)
    return value


def render_csv(
    lines: Iterable[ReconciliationLine],
    columns: dict[str, str] | None = None,
) -> str:
    """Render reconciliation lines to CSV text using the (default) column mapping."""
    columns = columns or DEFAULT_COLUMNS
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(list(columns.keys()))
    for line in lines:
        writer.writerow([_resolve(line, path) for path in columns.values()])
    return buffer.getvalue()
