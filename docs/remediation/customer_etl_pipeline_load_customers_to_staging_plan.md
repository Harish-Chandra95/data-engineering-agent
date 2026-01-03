# Remediation Plan: customer_etl_pipeline/load_customers_to_staging

**Strategy:** CREATE_TABLE

**Impact:** low

**Summary:** Implement table existence check and creation for 'analytics.customers_staging' to resolve 'Table not found' errors during ETL operations.

## Changes Made

1. `mock_data/sample_dags/customer_etl.py` - Add BigQuery table existence check and creation logic before data insertion.

## Database Changes

- CREATE `analytics.customers_staging`

## Testing Checklist

- [ ] Manually delete 'analytics.customers_staging' table in a dev BigQuery project (if it exists).
- [ ] Run the modified 'customer_etl.py' DAG in a dev environment.
- [ ] Verify that 'analytics.customers_staging' table is created with the correct schema and daily partitioning.
- [ ] Verify that data is successfully inserted into the newly created table.
- [ ] Run the DAG again to ensure it handles existing tables gracefully (no errors on subsequent runs).

## Rollback Plan

If issues occur: 1) Revert code changes in 'mock_data/sample_dags/customer_etl.py'. 2) If the table was created incorrectly, drop 'analytics.customers_staging' in BigQuery.

## Implementation Notes

Deploy during a low-traffic window. Monitor the first few DAG runs closely for successful table creation and data ingestion. Ensure the BigQuery service account used by the DAG has 'bigquery.tables.create' and 'bigquery.tables.get' permissions.
