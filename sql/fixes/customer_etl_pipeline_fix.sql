-- DDL Statements for customer_etl_pipeline
-- Generated: 2026-01-03T11:45:29.273406

-- Create the missing staging table with the expected schema and daily partitioning by the 'date' column.
CREATE TABLE IF NOT EXISTS analytics.customers_staging (
  customer_id STRING NOT NULL,
  email STRING,
  date DATE NOT NULL
) PARTITION BY date;

