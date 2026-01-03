# Remediation Plan: MANAGE_CONCURRENCY

**Summary:** Implement retry logic with exponential backoff for BigQuery writes to handle concurrent update errors.

**Impact:** medium

## Code Changes

### 1. mock_data/sample_dags/sales_report.py
**Type:** add | **Language:** python

Add necessary imports for tenacity retry library and BigQuery conflict exceptions.

**After:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import Conflict
```

### 2. mock_data/sample_dags/sales_report.py
**Type:** modify | **Language:** python

Apply retry decorator to the aggregate_sales_data function to handle transient concurrent write conflicts.

**Before:**
```python
def aggregate_sales_data(**context):
```

**After:**
```python
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(Conflict),
    reraise=True
)
def aggregate_sales_data(**context):
```

## Testing Steps

1. Install 'tenacity' library in the Airflow environment: `pip install tenacity`
2. Deploy the modified DAG to a development environment.
3. Manually trigger the DAG multiple times concurrently (e.g., by setting `max_active_runs` to a high number and triggering rapidly) to simulate high load.
4. Monitor DAG runs for successful completion and observe if retry attempts are logged for transient errors.
5. Verify that data is correctly written to 'analytics.sales_daily' without data loss or corruption after concurrent runs.

## Rollback Plan

If issues occur (e.g., new errors, performance degradation): 1) Revert the code changes in 'mock_data/sample_dags/sales_report.py' to the previous version. 2) Remove 'tenacity' from the Airflow environment's requirements if it's no longer needed by other DAGs.

## Implementation Notes

Ensure the 'tenacity' library is installed in the Airflow environment where the DAG will run. Deploy during a low-traffic window and monitor the first few runs closely for any unexpected behavior or increased task duration due to retries.
