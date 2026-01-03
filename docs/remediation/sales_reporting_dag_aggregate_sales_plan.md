# Remediation Plan: sales_reporting_dag/aggregate_sales

**Strategy:** REFACTOR_DATA_PIPELINE

**Impact:** medium

**Summary:** Refactor data pipeline to use a temporary staging table and a MERGE operation to prevent concurrent update errors when writing to analytics.sales_daily.

## Changes Made

1. `mock_data/sample_dags/sales_report.py` - Add BigQuery client and exception imports for data manipulation.
2. `mock_data/sample_dags/sales_report.py` - Refactor `aggregate_sales_data` to write to a date-specific staging table and then perform an atomic MERGE into the final `analytics.sales_daily` table, ensuring idempotency and preventing concurrent write conflicts.

## Database Changes

- CREATE `analytics.sales_daily`

## Testing Checklist

- [ ] Run the DAG in a development environment with the fix.
- [ ] Verify that the `analytics.sales_daily` table is created (if it doesn't exist) with the correct schema and partitioning.
- [ ] Verify that data is correctly inserted and/or updated in `analytics.sales_daily` for the execution date.
- [ ] Trigger the DAG multiple times for the *same execution date* (e.g., by clearing previous runs or backfilling) to simulate concurrent updates and confirm no serialization errors occur.
- [ ] Confirm that temporary staging tables (`analytics.sales_daily_staging_YYYYMMDD`) are created and subsequently deleted after successful merges.
- [ ] Validate data integrity and accuracy in `analytics.sales_daily` after multiple runs.

## Rollback Plan

If issues occur, revert the code changes in `mock_data/sample_dags/sales_report.py` to the previous version. If the `analytics.sales_daily` table schema was modified or created, assess data impact and potentially revert to a backup or previous schema version if necessary.

## Implementation Notes

Ensure the BigQuery connection is properly configured and accessible from the Airflow environment. Monitor BigQuery job costs and performance for the MERGE operations. Deploy during a low-traffic window and closely monitor the first few runs for any unexpected behavior or errors.
