"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Shell } from "@/components/Shell";
import { api } from "@/lib/client";

type Me = Awaited<ReturnType<typeof api.me>>;

export default function MyCampaignPage() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .me()
      .then(setMe)
      .catch((e) => {
        setError(e.message);
        router.push("/login");
      });
  }, [router]);

  if (error) return <Shell title="My campaign">Redirecting to sign in…</Shell>;
  if (!me) return <Shell title="My campaign">Loading…</Shell>;

  return (
    <Shell title="My campaign">
      <p>
        Signed in as <strong>{me.agent.full_name}</strong> ({me.agent.role}) · campaign{" "}
        <strong>{me.campaign.code}</strong> [{me.campaign.status}]
      </p>
      <h3>Warehouses</h3>
      <ul>
        {me.warehouses.map((w) => (
          <li key={w.id}>
            {w.whs_code} — {w.name}
          </li>
        ))}
      </ul>
      <nav style={{ display: "flex", gap: "var(--space-4)", marginTop: "var(--space-4)" }}>
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
