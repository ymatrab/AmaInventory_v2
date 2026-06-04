import { Card, Section } from "../components/ui";

// DESIGN-SLOT: analysis dashboard. Placeholder per architecture §10.1 — charts of
// gap trends, margin breaches, agent throughput land here when the design system
// and the analytics queries are defined.
export function Analysis() {
  return (
    <Section title="Analysis dashboard">
      <Card>
        <p style={{ color: "var(--color-text-muted)" }}>
          Placeholder. Future: gap-value trends per warehouse, margin-breach counts, agent
          throughput, recount rates. Wire to read-only aggregate endpoints.
        </p>
      </Card>
    </Section>
  );
}
