import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "@ama/tokens/tokens.css";
// Vendored @amafin/ui design system: its global stylesheet + runtime theme vars.
import "@amafin/ui/src/styles.css";
import { injectThemeVars } from "@amafin/ui/src/tokens/theme";
import "./index.css";
import { App } from "./App";
import { AuthProvider } from "./lib/auth";

injectThemeVars();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
