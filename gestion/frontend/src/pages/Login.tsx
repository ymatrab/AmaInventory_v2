import { useState } from "react";

import { useAuth } from "../lib/auth";
import { Button, Card, ErrorText, Input } from "../components/ui";

export function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 360, margin: "10vh auto" }}>
      <Card>
        <h1 style={{ color: "var(--color-brand)", marginTop: 0 }}>Gestion sign in</h1>
        <form
          onSubmit={submit}
          style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}
        >
          <Input
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button variant="primary" type="submit" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </Button>
          <ErrorText>{error}</ErrorText>
        </form>
      </Card>
    </div>
  );
}
