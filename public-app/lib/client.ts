"use client";

// Browser-side API helpers. Cookies are same-origin so they ride along
// automatically. Each call throws Error(message) on a non-2xx response.
async function jsonFetch<T>(url: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...opts,
    headers: { "Content-Type": "application/json", ...(opts?.headers ?? {}) },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = (data as { error?: { detail?: unknown } })?.error?.detail;
    throw new Error(typeof detail === "string" ? detail : `Request failed (${res.status})`);
  }
  return data as T;
}

export interface CountLineDTO {
  line_uid: string;
  warehouse_id: string;
  item_code: string;
  sku: string;
  qty_units: number;
  qty_packs: number;
  is_recount: boolean;
  flagged: boolean;
  version: number;
}

export const api = {
  login: (token: string, pin: string) =>
    jsonFetch("/api/auth/login", { method: "POST", body: JSON.stringify({ token, pin }) }),
  logout: () => jsonFetch("/api/auth/logout", { method: "POST" }),
  me: () =>
    jsonFetch<{
      agent: { id: string; full_name: string; role: string };
      campaign: { code: string; status: string; open: boolean };
      warehouses: { id: string; whs_code: string; name: string }[];
    }>("/api/me"),
  items: () =>
    jsonFetch<{
      items: {
        item_code: string;
        sku: string;
        description: string;
        color_parfum: string;
        units_per_pack: number;
      }[];
    }>("/api/items"),
  mine: () =>
    jsonFetch<{ lines: CountLineDTO[]; progress: { total: number; flagged: number } }>(
      "/api/counts/mine",
    ),
  recount: () => jsonFetch<{ lines: CountLineDTO[] }>("/api/recount"),
  submit: (payload: {
    line_uid?: string;
    warehouse_id: string;
    item_code: string;
    sku: string;
    qty_units: number;
    qty_packs: number;
  }) =>
    jsonFetch<{ line: CountLineDTO }>("/api/counts", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
