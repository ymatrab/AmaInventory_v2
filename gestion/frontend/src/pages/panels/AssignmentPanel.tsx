import { useCallback, useEffect, useState } from "react";

import { api, type Assignment, type Campaign, type FieldUser, type Me } from "../../lib/api";
import { Badge, Button, Card, Table, td } from "../../components/ui";

export function AssignmentPanel({ campaign, me }: { campaign: Campaign; me: Me | null }) {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [fieldUsers, setFieldUsers] = useState<FieldUser[]>([]);
  const [warehouse, setWarehouse] = useState<number | "">("");
  const [user, setUser] = useState<number | "">("");

  const reload = useCallback(() => {
    api
      .assignments(campaign.id)
      .then(setAssignments)
      .catch(() => setAssignments([]));
  }, [campaign.id]);

  useEffect(() => {
    reload();
    api
      .fieldUsers()
      .then(setFieldUsers)
      .catch(() => setFieldUsers([]));
  }, [reload]);

  const canAssign = !!me && (me.is_inventory_responsible || me.is_cdg);
  const canConfirm = !!me && me.is_audit;
  const sel = {
    padding: "var(--space-2)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
  };

  async function add() {
    if (!warehouse || !user) return;
    await api.createAssignment({ campaign: campaign.id, warehouse, field_user: user });
    setWarehouse("");
    setUser("");
    reload();
  }

  return (
    <Card>
      <div
        style={{
          display: "flex",
          gap: "var(--space-2)",
          marginBottom: "var(--space-4)",
          alignItems: "center",
        }}
      >
        <select
          value={warehouse}
          onChange={(e) => setWarehouse(Number(e.target.value))}
          style={sel}
        >
          <option value="">Warehouse…</option>
          {campaign.warehouses.map((w) => (
            <option key={w.id} value={w.id}>
              {w.whs_code}
            </option>
          ))}
        </select>
        <select value={user} onChange={(e) => setUser(Number(e.target.value))} style={sel}>
          <option value="">Field user…</option>
          {fieldUsers.map((u) => (
            <option key={u.id} value={u.id}>
              {u.matricule} — {u.full_name} ({u.role})
            </option>
          ))}
        </select>
        <Button disabled={!canAssign} onClick={add}>
          Assign
        </Button>
        <Button
          variant="primary"
          disabled={!canConfirm}
          onClick={() => api.confirmAssignments(campaign.id).then(reload)}
        >
          Confirm all (Audit)
        </Button>
      </div>

      <Table head={["Warehouse", "Agent", "Role", "Confirmed", ""]}>
        {assignments.map((a) => (
          <tr key={a.id}>
            <td style={td}>{a.whs_code}</td>
            <td style={td}>
              {a.matricule} — {a.full_name}
            </td>
            <td style={td}>{a.full_name}</td>
            <td style={td}>{a.confirmed ? <Badge>confirmed</Badge> : "—"}</td>
            <td style={td}>
              <Button
                variant="danger"
                disabled={!canAssign}
                onClick={() => api.deleteAssignment(a.id).then(reload)}
              >
                Remove
              </Button>
            </td>
          </tr>
        ))}
        {assignments.length === 0 && (
          <tr>
            <td style={td} colSpan={5}>
              No assignments yet.
            </td>
          </tr>
        )}
      </Table>
    </Card>
  );
}
