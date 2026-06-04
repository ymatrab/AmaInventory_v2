import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

// The shared @ama/tokens package lives at the repo root (../../packages),
// outside this Vite project root, so allow serving from there.
// /api and /admin are proxied to the Django backend so the SPA calls the API
// same-origin — session cookies + CSRF work without cross-origin cookie hassle.
// In Docker the backend is the `web` service; override with VITE_PROXY_TARGET.
const proxyTarget = process.env.VITE_PROXY_TARGET ?? "http://web:8000";

export default defineConfig({
  plugins: [react()],
  // @amafin/ui ships TSX source (vendored at ../../packages/ui). Exclude it from
  // dep pre-bundling so Vite compiles it through the React/esbuild pipeline; its
  // own runtime deps resolve from packages/ui/node_modules. Dedupe React so the
  // library and the app share one copy (it lists react as a peer dependency).
  optimizeDeps: { exclude: ["@amafin/ui"] },
  resolve: { dedupe: ["react", "react-dom", "react/jsx-runtime"] },
  server: {
    host: true,
    port: 5174,
    fs: { allow: [resolve(__dirname, "../..")] },
    proxy: {
      "/api": { target: proxyTarget, changeOrigin: true },
      "/admin": { target: proxyTarget, changeOrigin: true },
      "/static": { target: proxyTarget, changeOrigin: true },
    },
  },
});
