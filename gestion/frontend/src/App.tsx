import { Navigate, Route, Routes } from "react-router-dom";

import { Shell } from "./components/Shell";
import { useAuth } from "./lib/auth";
import { Login } from "./pages/Login";
import { CampaignsOverview } from "./pages/CampaignsOverview";
import { CreateCampaign } from "./pages/CreateCampaign";
import { CampaignDetail } from "./pages/CampaignDetail";
import { History } from "./pages/History";
import { Analysis } from "./pages/Analysis";

export function App() {
  const { me, loading } = useAuth();

  if (loading) return <p style={{ padding: "var(--space-6)" }}>Loading…</p>;
  if (!me) return <Login />;

  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Navigate to="/campaigns" replace />} />
        <Route path="/campaigns" element={<CampaignsOverview />} />
        <Route path="/campaigns/new" element={<CreateCampaign />} />
        <Route path="/campaigns/:id" element={<CampaignDetail />} />
        <Route path="/history" element={<History />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="*" element={<Navigate to="/campaigns" replace />} />
      </Route>
    </Routes>
  );
}
