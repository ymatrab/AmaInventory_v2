import { useEffect, useState } from "react";

import { api, type AuditEntry, type Campaign } from "../lib/api";
import { Badge, Card, Section, Table, td } from "../components/ui";

export function History() {
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [archived, setArchived] = useState<Campaign[]>([]);

  useEffect(() => {
    api
      .audit()
      .then(setAudit)
      .catch(() => setAudit([]));
    api
      .campaigns()
      .then((cs) => setArchived(cs.filter((c) => c.status === "CLOSED" || c.status === "ARCHIVED")))
      .catch(() => setArchived([]));
  }, []);

  return (
    <>
      <Section title="Closed / archived campaigns">
        <Card>
          <Table head={["Code", "Status", "Closed"]}>
            {archived.map((c) => (
              <tr key={c.id}>
                <td style={td}>{c.code}</td>
                <td style={td}>
                  <Badge>{c.status_display}</Badge>
                </td>
                <td style={td}>{c.close_at ? new Date(c.close_at).toLocaleString() : "—"}</td>
              </tr>
            ))}
            {archived.length === 0 && (
              <tr>
                <td style={td} colSpan={3}>
                  None yet.
                </td>
              </tr>
            )}
          </Table>
        </Card>
      </Section>

      <Section title="Audit log">
        <Card>
          <Table head={["When", "Actor", "Action", "Entity"]}>
            {audit.map((a) => (
              <tr key={a.id}>
                <td style={td}>{new Date(a.timestamp).toLocaleString()}</td>
                <td style={td}>{a.actor ?? "—"}</td>
                <td style={td}>{a.action}</td>
                <td style={td}>
                  {a.entity}#{a.entity_id}
                </td>
              </tr>
            ))}
          </Table>
        </Card>
      </Section>
    </>
  );
}
