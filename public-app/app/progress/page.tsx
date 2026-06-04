"use client";

import { useEffect, useState } from "react";

import { Shell } from "@/components/Shell";
import { api, type CountLineDTO } from "@/lib/client";

export default function ProgressPage() {
  const [lines, setLines] = useState<CountLineDTO[] | null>(null);
  const [progress, setProgress] = useState<{ total: number; flagged: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .mine()
      .then((d) => {
        setLines(d.lines);
        setProgress(d.progress);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <Shell title="Progress">{error}</Shell>;
  if (!lines || !progress) return <Shell title="Progress">Loading…</Shell>;

  return (
    <Shell title="Progress">
      <p>
        {progress.total} line(s) submitted · {progress.flagged} flagged for re-count.
      </p>
      <ul>
        {lines.map((l) => (
          <li key={l.line_uid}>
            {l.item_code}/{l.sku}: {l.qty_units} units + {l.qty_packs} packs (v{l.version})
            {l.flagged ? " · flagged" : ""}
          </li>
        ))}
      </ul>
    </Shell>
  );
}
