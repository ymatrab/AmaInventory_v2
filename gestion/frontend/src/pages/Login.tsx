import { useState } from "react";

// Demo of the vendored @amafin/ui design system (deep imports keep the build
// graph lean — the whole library is also available via `import { X } from "@amafin/ui"`).
import { Button } from "@amafin/ui/src/atoms/Button";
import { InputField } from "@amafin/ui/src/molecules/InputField";
import { AlertMessage } from "@amafin/ui/src/molecules/AlertMessage";

import { useAuth } from "../lib/auth";

export function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
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

  const onEnter = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") submit();
  };

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
      <div className="login-card" style={{ width: 380 }}>
        <div className="login-card-header">
          <h1 className="login-title">Gestion sign in</h1>
          <p className="login-subtitle">Inventory control — internal app</p>
        </div>

        <AlertMessage message={error ?? undefined} />

        <InputField
          label="Username"
          inputProps={{
            value: username,
            onChange: (e) => setUsername(e.target.value),
            placeholder: "username",
            onKeyDown: onEnter,
          }}
        />
        <InputField
          label="Password"
          rightSlot={
            <button
              type="button"
              className="icon-button"
              onClick={() => setShowPassword((s) => !s)}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          }
          inputProps={{
            type: showPassword ? "text" : "password",
            value: password,
            onChange: (e) => setPassword(e.target.value),
            placeholder: "password",
            onKeyDown: onEnter,
          }}
        />

        <Button variant="login" block onClick={submit} disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </Button>
      </div>
    </div>
  );
}
