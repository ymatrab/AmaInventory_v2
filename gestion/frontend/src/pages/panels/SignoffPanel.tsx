import { useCallback, useEffect, useState } from "react";

import { api, type Campaign, type SignOff } from "../../lib/api";
import { Button, Card, Table, td } from "../../components/ui";

// DESIGN-SLOT: scanned-sheet upload UI. Backend SignOff has a `document` field;
// wire a file upload here when the design system provides the control.
export function SignoffPanel({ campaign }: { campaign: Campaign }) {
  const [signoffs, setSignoffs] = useState<SignOff[]>([]);

  const reload = useCallback(() => {
    api
      .signoffs(campaign.id)
      .then(setSignoffs)
      .catch(() => setSignoffs([]));
  }, [campaign.id]);

  useEffect(reload, [reload]);

  const existing = new Map(signoffs.map((s) => [s.warehouse, s]));

  async function ensure(warehouseId: number): Promise<SignOff> {
    const found = existing.get(warehouseId);
    if (found) return found;
    return api.createSignoff({ campaign: campaign.id, warehouse: warehouseId });
  }

  async function toggle(warehouseId: number, field: keyof SignOff, value: boolean) {
    const s = await ensure(warehouseId);
    await api.updateSignoff(s.id, { [field]: value });
    reload();
  }

  return (
    <Card>
      <Table head={["Warehouse", "Agent signed", "Warehouseman signed", "Received"]}>
        {campaign.warehouses.map((w) => {
          const s = existing.get(w.id);
          return (
            <tr key={w.id}>
              <td style={td}>{w.whs_code}</td>
              <td style={td}>
                <input
                  type="checkbox"
                  checked={!!s?.agent_signed}
                  onChange={(e) => toggle(w.id, "agent_signed", e.target.checked)}
                />
              </td>
              <td style={td}>
                <input
                  type="checkbox"
                  checked={!!s?.warehouseman_signed}
                  onChange={(e) => toggle(w.id, "warehouseman_signed", e.target.checked)}
                />
              </td>
              <td style={td}>
                <Button onClick={() => toggle(w.id, "received", !s?.received)}>
                  {s?.received ? "Received ✓" : "Mark received"}
                </Button>
              </td>
            </tr>
          );
        })}
      </Table>
    </Card>
  );
}
