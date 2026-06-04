// Centralized API access for the gestion SPA (CLAUDE.md §6: data logic lives
// here, separate from presentation). Calls are same-origin via the Vite proxy,
// so the session cookie rides along; unsafe methods send the CSRF token.

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    detail: string,
  ) {
    super(detail);
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (method !== "GET") {
    const csrf = getCookie("csrftoken");
    if (csrf) headers["X-CSRFToken"] = csrf;
  }
  const res = await fetch(`/api${path}`, {
    method,
    headers,
    credentials: "same-origin",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = (data as { error?: { code?: string; detail?: string } }).error;
    throw new ApiError(
      res.status,
      err?.code ?? "error",
      err?.detail ?? `Request failed (${res.status})`,
    );
  }
  return data as T;
}

export const http = {
  get: <T>(p: string) => request<T>("GET", p),
  post: <T>(p: string, body?: unknown) => request<T>("POST", p, body),
  patch: <T>(p: string, body?: unknown) => request<T>("PATCH", p, body),
  del: <T>(p: string) => request<T>("DELETE", p),
};

// --- Types (only the fields the UI uses) ---
export interface Me {
  username: string;
  is_superuser: boolean;
  groups: string[];
  is_cdg: boolean;
  is_audit: boolean;
  is_inventory_responsible: boolean;
}

export interface Campaign {
  id: number;
  code: string;
  type: string;
  trigger: string;
  scope: string;
  status: string;
  status_display: string;
  open_at: string | null;
  close_at: string | null;
  created_at: string;
  warehouses: { id: number; whs_code: string; name: string }[];
}

interface Paginated<T> {
  count: number;
  results: T[];
}

export interface Warehouse {
  id: number;
  whs_code: string;
  name: string;
  city: string;
  active: boolean;
}
export interface FieldUser {
  id: number;
  matricule: string;
  full_name: string;
  role: string;
  active: boolean;
}
export interface Assignment {
  id: number;
  campaign: number;
  warehouse: number;
  whs_code: string;
  field_user: number;
  matricule: string;
  full_name: string;
  confirmed: boolean;
}
export interface ReconLine {
  id: number;
  item_code: string;
  sku: string;
  physical_qty: string;
  system_qty: string;
  gap_qty: string;
  gap_value: string;
  within_margin: boolean;
}
export interface Reconciliation {
  id: number;
  warehouse: number;
  whs_code: string;
  value_margin: string;
  lines: ReconLine[];
}
export interface CsvExport {
  id: number;
  whs_code: string | null;
  generated_at: string;
  file_ref: string;
}
export interface SignOff {
  id: number;
  campaign: number;
  warehouse: number;
  whs_code: string;
  agent_signed: boolean;
  warehouseman_signed: boolean;
  received: boolean;
}
export interface AuditEntry {
  id: number;
  actor: string | null;
  action: string;
  entity: string;
  entity_id: string;
  timestamp: string;
}

const list = <T>(p: string) => http.get<Paginated<T>>(p).then((r) => r.results);

// --- API surface used by the pages ---
export const api = {
  csrf: () => http.get("/auth/csrf/"),
  login: (username: string, password: string) =>
    http.post<Me>("/auth/login/", { username, password }),
  logout: () => http.post("/auth/logout/"),
  me: () => http.get<Me>("/auth/me/"),

  campaigns: () => list<Campaign>("/campaigns/"),
  campaign: (id: number) => http.get<Campaign>(`/campaigns/${id}/`),
  createCampaign: (body: Record<string, unknown>) => http.post<Campaign>("/campaigns/", body),
  armCampaign: (id: number) => http.post(`/campaigns/${id}/arm/`),
  genCredentials: (id: number) =>
    http.post<{ credentials: { matricule: string; pin: string; token: string }[] }>(
      `/campaigns/${id}/generate_credentials/`,
    ),
  pushSetup: (id: number) => http.post(`/campaigns/${id}/push_setup/`),
  openCampaign: (id: number) => http.post<Campaign>(`/campaigns/${id}/open/`),
  closeCampaign: (id: number) => http.post<Campaign>(`/campaigns/${id}/close/`),
  extendCampaign: (id: number, close_at: string) =>
    http.post<Campaign>(`/campaigns/${id}/extend/`, { close_at }),
  syncNow: (id: number) => http.post<{ rows: number }>(`/campaigns/${id}/sync_now/`),

  warehouses: () => list<Warehouse>("/warehouses/"),
  fieldUsers: () => list<FieldUser>("/field-users/"),

  assignments: (campaign: number) => list<Assignment>(`/assignments/?campaign=${campaign}`),
  createAssignment: (body: Record<string, unknown>) => http.post<Assignment>("/assignments/", body),
  deleteAssignment: (id: number) => http.del(`/assignments/${id}/`),
  confirmAssignments: (campaign: number) =>
    http.post<{ confirmed: number }>("/assignments/confirm/", { campaign }),

  counts: (campaign: number) => list(`/counts/?campaign=${campaign}`),
  monitor: (campaign: number) =>
    http.get<{
      warehouses: { whs_code: string; lines: number; flagged: number; last_update: string }[];
    }>(`/counts/monitor/?campaign=${campaign}`),
  kpi: (campaign: number) =>
    http.get<{
      agents: {
        counted_by__matricule: string;
        counted_by__full_name: string;
        lines: number;
        units: string;
      }[];
    }>(`/counts/kpi/?campaign=${campaign}`),

  reconciliations: (campaign: number) =>
    list<Reconciliation>(`/reconciliations/?campaign=${campaign}`),
  buildRecon: (campaign: number, warehouse: number) =>
    http.post<Reconciliation>("/reconciliations/build/", { campaign, warehouse }),
  setMargin: (campaign: number, warehouse: number, value_margin: string) =>
    http.post<Reconciliation>("/reconciliations/set_margin/", {
      campaign,
      warehouse,
      value_margin,
    }),
  flagRecount: (campaign: number, warehouse: number, item_codes: string[]) =>
    http.post("/reconciliations/flag_recount/", { campaign, warehouse, item_codes }),

  exports: (campaign: number) => list<CsvExport>(`/exports/?campaign=${campaign}`),
  generateExport: (campaign: number, warehouse?: number) =>
    http.post<CsvExport>("/exports/generate/", { campaign, warehouse }),
  downloadExportUrl: (id: number) => `/api/exports/${id}/download/`,

  signoffs: (campaign: number) => list<SignOff>(`/signoffs/?campaign=${campaign}`),
  createSignoff: (body: Record<string, unknown>) => http.post<SignOff>("/signoffs/", body),
  updateSignoff: (id: number, body: Record<string, unknown>) =>
    http.patch<SignOff>(`/signoffs/${id}/`, body),

  audit: (entity?: string, entityId?: string) =>
    list<AuditEntry>(
      `/audit/${entity ? `?entity=${entity}${entityId ? `&entity_id=${entityId}` : ""}` : ""}`,
    ),
};

export { ApiError };
