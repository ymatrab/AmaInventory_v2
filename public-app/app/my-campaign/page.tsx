import Link from "next/link";

import { Shell } from "@/components/Shell";

// My campaign / WHS — shows the agent's assignment + instructions (wired in Phase 5).
// DESIGN-SLOT: assignment overview.
export default function MyCampaignPage() {
  return (
    <Shell title="My campaign">
      <p style={{ color: "var(--color-text-muted)" }}>
        Your assigned warehouse and counting instructions appear here once signed in.
      </p>
      <nav style={{ display: "flex", gap: "var(--space-4)" }}>
        <Link href="/count" style={{ color: "var(--color-brand)" }}>
          Count entry →
        </Link>
        <Link href="/recount" style={{ color: "var(--color-brand)" }}>
          Re-count →
        </Link>
        <Link href="/progress" style={{ color: "var(--color-brand)" }}>
          Progress →
        </Link>
      </nav>
    </Shell>
  );
}
