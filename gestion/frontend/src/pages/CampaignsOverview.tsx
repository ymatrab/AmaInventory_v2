import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { api, type Campaign } from "../lib/api";
import { Badge, Button, Section, Table, td } from "../components/ui";

export function CampaignsOverview() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .campaigns()
      .then(setCampaigns)
      .catch(() => setCampaigns([]));
  }, []);

  return (
    <Section
      title="Campaigns"
      actions={
        <Button variant="primary" onClick={() => navigate("/campaigns/new")}>
          New campaign
        </Button>
      }
    >
      <Table head={["Code", "Type", "Status", "Window", "Warehouses"]}>
        {campaigns.map((c) => (
          <tr key={c.id}>
            <td style={td}>
              <Link to={`/campaigns/${c.id}`}>{c.code}</Link>
            </td>
            <td style={td}>{c.type}</td>
            <td style={td}>
              <Badge>{c.status_display}</Badge>
            </td>
            <td style={td}>
              {c.open_at ? new Date(c.open_at).toLocaleDateString() : "—"} →{" "}
              {c.close_at ? new Date(c.close_at).toLocaleDateString() : "—"}
            </td>
            <td style={td}>{c.warehouses.map((w) => w.whs_code).join(", ") || "—"}</td>
          </tr>
        ))}
        {campaigns.length === 0 && (
          <tr>
            <td style={td} colSpan={5}>
              No campaigns yet.
            </td>
          </tr>
        )}
      </Table>
    </Section>
  );
}
