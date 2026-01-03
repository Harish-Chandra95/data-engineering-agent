-- DDL Statements for customer_etl_pipeline
-- Generated: 2026-01-03T11:33:10.381077

-- Create the missing staging table 'analytics.customers_staging' with the schema derived from 'raw.customers' and the expected schema.
CREATE TABLE IF NOT EXISTS analytics.customers_staging (
  customer_id STRING NOT NULL,
  email STRING
);

