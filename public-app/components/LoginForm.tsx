"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api } from "@/lib/client";

// DESIGN-SLOT: per-agent login (link prefills token; agent enters PIN).
export function LoginForm({ token: presetToken }: { token?: string }) {
  const router = useRouter();
  const [token, setToken] = useState(presetToken ?? "");
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.login(token, pin);
      router.push("/my-campaign");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} style={{ display: "grid", gap: "var(--space-3)", maxWidth: 320 }}>
      {!presetToken && (
        <label style={{ display: "grid", gap: "var(--space-1)" }}>
          <span>Access token</span>
          <input
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="from your counting link"
            style={{ padding: "var(--space-2)", borderRadius: "var(--radius-sm)" }}
          />
        </label>
      )}
      <label style={{ display: "grid", gap: "var(--space-1)" }}>
        <span>PIN</span>
        <input
          value={pin}
          onChange={(e) => setPin(e.target.value)}
          inputMode="numeric"
          autoComplete="one-time-code"
          style={{ padding: "var(--space-2)", borderRadius: "var(--radius-sm)" }}
        />
      </label>
      {error && <p style={{ color: "var(--color-danger)", margin: 0 }}>{error}</p>}
      <button
        type="submit"
        disabled={busy || !token || !pin}
        style={{
          padding: "var(--space-2)",
          background: "var(--color-brand)",
          color: "var(--color-brand-contrast)",
          border: "none",
          borderRadius: "var(--radius-sm)",
          cursor: busy ? "default" : "pointer",
        }}
      >
        {busy ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
