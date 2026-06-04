import Link from "next/link";

import { Shell } from "@/components/Shell";

// Landing / "no active campaign" — the default closed state.
// DESIGN-SLOT: brand landing screen.
export default function Home() {
  return (
    <Shell title="Inventory — Field App">
      <p style={{ color: "var(--color-text-muted)" }}>
        The app opens during a campaign window. If you have a counting link, open it to sign in.
      </p>
      <p>
        <Link href="/login" style={{ color: "var(--color-brand)" }}>
          Go to sign in →
        </Link>
      </p>
    </Shell>
  );
}
