# Remediation Plan: ftp_file_ingestion/download_customer_files

**Strategy:** FIX_CONNECTION

**Impact:** medium

**Summary:** Implement retry logic with exponential backoff for SFTP connection to handle transient network issues and improve connection robustness.

## Changes Made

1. `mock_data/sample_dags/ftp_ingestion.py` - Add `tenacity` and `paramiko.ssh_exception` imports for retry logic.
2. `mock_data/sample_dags/ftp_ingestion.py` - Implement `tenacity` retry logic with exponential backoff and increased timeout for SFTP connection within `download_files` function.

## Testing Checklist

- [ ] Ensure `tenacity` library is installed in the Airflow environment.
- [ ] Deploy the modified DAG to a development environment.
- [ ] Simulate SFTP server unavailability (e.g., temporarily block port 22 outbound from Airflow worker) and verify the task retries connection attempts with exponential backoff before failing.
- [ ] Verify successful SFTP connection and file download when the SFTP server is available.
- [ ] Monitor Airflow logs for `Failed to connect to SFTP after multiple retries` message on connection failure, and for successful completion messages on success.

## Rollback Plan

If issues occur, revert the code changes in `mock_data/sample_dags/ftp_ingestion.py` to the previous version. This will remove the retry logic and revert to the original connection behavior.

## Implementation Notes

Ensure `tenacity` library is installed in the Airflow environment (`pip install tenacity`). Deploy during a low-traffic window. Monitor DAG runs closely after deployment to confirm connection stability and file ingestion.
