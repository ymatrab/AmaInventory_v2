import { useEffect, useState } from "react";

import { api, type Campaign } from "../../lib/api";
import { Card, Table, td } from "../../components/ui";

interface AgentRow {
  counted_by__matricule: string;
  counted_by__full_name: string;
  lines: number;
  units: string;
}

export function KpiPanel({ campaign }: { campaign: Campaign }) {
  const [agents, setAgents] = useState<AgentRow[]>([]);

  useEffect(() => {
    api
      .kpi(campaign.id)
      .then((r) => setAgents(r.agents))
      .catch(() => setAgents([]));
  }, [campaign.id]);

  return (
    <Card>
      <Table head={["Agent", "Name", "Lines counted", "Total units"]}>
        {agents.map((a) => (
          <tr key={a.counted_by__matricule}>
            <td style={td}>{a.counted_by__matricule}</td>
            <td style={td}>{a.counted_by__full_name}</td>
            <td style={td}>{a.lines}</td>
            <td style={td}>{a.units}</td>
          </tr>
        ))}
        {agents.length === 0 && (
          <tr>
            <td style={td} colSpan={4}>
              No attributed counts yet.
            </td>
          </tr>
        )}
      </Table>
    </Card>
  );
}
