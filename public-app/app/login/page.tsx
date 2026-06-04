import { LoginForm } from "@/components/LoginForm";
import { Shell } from "@/components/Shell";

// Manual sign in (token + PIN). The usual path is the per-agent magic link.
export default function LoginPage() {
  return (
    <Shell title="Sign in">
      <p style={{ color: "var(--color-text-muted)" }}>
        Open your personal counting link, or enter your access token and PIN below.
      </p>
      <LoginForm />
    </Shell>
  );
}
