-- system_stock.sql — READ-ONLY query returning theoretical (system) stock.
--
-- Contract: return these columns (names matter), one row per item in the warehouse:
--   warehouse_code, item_code, sku, system_qty, unit_value
-- Bind parameter: warehouse_code (the query is run once per warehouse).
--
-- Keep this SELECT-only. The connection is opened read-only; never mutate SAP.
--
-- ───────────────────────────────────────────────────────────────────────────
-- EXAMPLE for SAP Business One (replace with your real schema / adjust columns).
-- OITW = item-per-warehouse stock, OWHS = warehouses, OITM = item master.
--
--   SELECT
--       t."WhsCode"   AS warehouse_code,
--       t."ItemCode"  AS item_code,
--       t."ItemCode"  AS sku,          -- map SKU/variant if tracked separately
--       t."OnHand"    AS system_qty,
--       i."AvgPrice"  AS unit_value
--   FROM OITW t
--   JOIN OWHS w ON w."WhsCode"  = t."WhsCode"
--   JOIN OITM i ON i."ItemCode" = t."ItemCode"
--   WHERE t."WhsCode" = :warehouse_code
--     AND i."validFor" = 'Y';
-- ───────────────────────────────────────────────────────────────────────────
--
-- TODO(SAP): replace the placeholder below with the real query.
-- The placeholder returns zero rows so the seam is safe to call before wiring.
SELECT
    ''  AS warehouse_code,
    ''  AS item_code,
    ''  AS sku,
    0   AS system_qty,
    0   AS unit_value
WHERE 1 = 0;
