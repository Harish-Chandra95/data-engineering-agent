-- DDL Statements for customer_etl_pipeline
-- Generated: 2026-01-03T11:21:22.610000

-- Create missing staging table with expected schema and daily partitioning.
CREATE TABLE IF NOT EXISTS analytics.customers_staging (
  customer_id STRING NOT NULL,
  email STRING,
  created_at TIMESTAMP NOT NULL,
  country STRING,
  date DATE NOT NULL
) PARTITION BY date;

