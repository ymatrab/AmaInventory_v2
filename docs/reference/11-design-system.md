# 11 · Design System (`@amafin/ui`)

[← Documentation index](../DOCUMENTATION.md)

The gestion SPA can use **`@amafin/ui`** — an atomic-design React component library (atoms /
molecules / organisms / templates / layouts) **vendored** into this repo at
[`packages/ui/`](../../packages/ui/). This is the design system CLAUDE.md §6 anticipated ("the user
will add their own React components + design system after scaffolding").

> Sourced from `github.com/nin-oh/enosis-frontend` (`packages/ui`). Vendored = the source lives in
> our repo as a workspace package; there is no live GitHub dependency at build time.

---

## 1. What it is

- ~80 components: `atoms` (Button, Input, Select, Badge, Icon, …), `molecules` (InputField,
  AlertMessage, SectionCard, FormField, …), `organisms` (DataTable, LoginForm, KpiGrid, Navbar, …),
  plus templates/layouts/hooks.
- Styled with **plain CSS classes + CSS variables** — a single global `src/styles.css` plus runtime
  theme variables injected by `injectThemeVars()`. **No Tailwind is required** to consume it.
- Ships **TypeScript source** (`main: src/index.ts`), compiled by the consumer's bundler (Vite).
- Peer dependency **React 19** (the gestion SPA was upgraded 18 → 19 for this).

---

## 2. How it's wired into the gestion SPA

| Concern | How |
|---------|-----|
| Package | `packages/ui/` (name `@amafin/ui`), referenced by the frontend as `"@amafin/ui": "file:../../packages/ui"`. |
| Its own deps | Installed into `packages/ui/node_modules` (runtime deps only; **no** React there — it's a peer). Vite follows the symlink's real path and resolves them from there. |
| React dedupe | `vite.config.ts` → `resolve.dedupe: ["react","react-dom","react/jsx-runtime"]` so the library and app share one React. |
| Source compile | `vite.config.ts` → `optimizeDeps.exclude: ["@amafin/ui"]` so Vite runs its TSX through the React/esbuild pipeline (not dep pre-bundling). `server.fs.allow` already covers the repo root. |
| Types for `tsc` | `packages/ui` carries `@types/react`/`@types/react-dom` (type-only, no runtime React) so the app's `tsc` can type-check the imported source. |
| Tree-shaking | `packages/ui/package.json` has `"sideEffects": ["**/*.css"]` so unused components (and heavy deps like recharts/xlsx) drop from the bundle. |
| Styles + theme | `main.tsx` imports `@amafin/ui/src/styles.css` and calls `injectThemeVars()` once at startup. |
| Self-contained tsconfig | `packages/ui/tsconfig.json` was de-`extends`'d (the upstream `tsconfig.base.json` wasn't vendored). |

`packages/ui/node_modules` and any `dist/` are gitignored; the **source** is committed.

---

## 3. Using it in a page

```tsx
// Deep imports keep the build graph lean (recommended for a few components):
import { Button } from "@amafin/ui/src/atoms/Button";
import { InputField } from "@amafin/ui/src/molecules/InputField";

// Or the barrel (pulls the whole library graph — fine, tree-shaken at build):
import { Button, InputField, AlertMessage } from "@amafin/ui";
```

CSS classes like `login-card`, `button--primary`, `input-field` come from the global stylesheet
imported in `main.tsx`. Theme colors are CSS variables (`--color-primary`, …) defined by
`injectThemeVars()`.

**Live example:** the gestion **Login** page ([`src/pages/Login.tsx`](../../gestion/frontend/src/pages/Login.tsx))
is built from `@amafin/ui` (`Button` + `InputField` + `AlertMessage`). The other gestion pages still
use the local `components/ui.tsx` primitives — migrate them incrementally.

> **Type note:** the app type-checks the *imported* component files (deep imports keep that to a
> handful). Importing components that pull heavy deps (recharts/xlsx organisms) will require those
> to be type-clean too; deep-import only what you use, or generate `.d.ts` from the library later.

---

## 4. Updating the vendored copy

It's a manual re-vendor (no live dependency):

```bash
git clone --depth 1 https://github.com/nin-oh/enosis-frontend.git /tmp/enosis
rm -rf packages/ui/src && cp -R /tmp/enosis/packages/ui/src packages/ui/src
# Re-apply local adjustments: self-contained tsconfig (no extends), and reinstall:
docker compose -f gestion/docker-compose.yml run --rm -w /workspace/packages/ui frontend \
  npm install --omit=dev --legacy-peer-deps
```

Then rebuild the frontend (`make lint` / `npm run build`) and re-check the pages you've migrated.

---

## 5. Two design systems, for now

- **`packages/tokens`** (`@ama/tokens`) — the original minimal CSS-variable tokens, used by the
  remaining gestion pages and the public app.
- **`packages/ui`** (`@amafin/ui`) — the richer component library, used by the Login page and
  available for the rest.

They coexist (different CSS-variable names). As pages migrate to `@amafin/ui`, the `@ama/tokens`
usage in the gestion SPA can shrink. The **public app** still uses `@ama/tokens` (a separate
Next.js project; adopting `@amafin/ui` there would be a separate task).
</content>
