-- DDL Statements for sales_reporting_dag
-- Generated: 2026-01-03T11:46:16.119799

-- Ensure the final `analytics.sales_daily` table is partitioned by date to support efficient MERGE operations and idempotent daily updates.
CREATE TABLE IF NOT EXISTS analytics.sales_daily (
  product_id INT64 NOT NULL,
  sales INT64 NOT NULL,
  region STRING NOT NULL,
  date DATE NOT NULL
)
PARTITION BY date;

