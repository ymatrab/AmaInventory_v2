import { LoginForm } from "@/components/LoginForm";
import { Shell } from "@/components/Shell";

// Magic link /c/{campaignCode}/a/{token} — prefills identity (token); agent enters PIN.
export default function MagicLinkPage({ params }: { params: { campaign: string; token: string } }) {
  return (
    <Shell title="Sign in">
      <p style={{ color: "var(--color-text-muted)" }}>
        Campaign <strong>{params.campaign}</strong>. Enter your PIN to start counting.
      </p>
      <LoginForm token={params.token} />
    </Shell>
  );
}
