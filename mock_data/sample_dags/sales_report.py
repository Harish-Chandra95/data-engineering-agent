def aggregate_sales_data(**context):
    """Aggregate sales by product and region and merge into final table."""
    execution_date = context['ds'] # 'YYYY-MM-DD'
    execution_date_nodash = context['ds_nodash'] # 'YYYYMMDD'

    client = bigquery.Client()
    
    final_table_id = 'analytics.sales_daily'
    staging_table_id = f'analytics.sales_daily_staging_{execution_date_nodash}'

    # Simulated data processing
    df = pd.DataFrame({
        'product_id': [1, 2, 3],
        'sales': [100, 200, 300],
        'region': ['US', 'EU', 'APAC']
    })
    
    # Add the date column for partitioning and merging
    df['date'] = pd.to_datetime(execution_date).date()

    try:
        # 1. Write to a temporary staging table.
        #    Using if_exists='replace' for the staging table ensures idempotency
        #    if the task retries, it just overwrites its own staging data.
        df.to_gbq(staging_table_id, project_id=client.project, if_exists='replace')
        print(f"Data successfully written to staging table: {staging_table_id}")

        # 2. Perform a MERGE operation from staging to final table.
        #    This handles inserts for new dates and updates for existing data
        #    for the specific date, preventing concurrent append issues.
        merge_query = f"""
            MERGE INTO `{final_table_id}` AS T
            USING `{staging_table_id}` AS S
            ON T.product_id = S.product_id AND T.region = S.region AND T.date = S.date
            WHEN MATCHED THEN
                UPDATE SET T.sales = S.sales
            WHEN NOT MATCHED THEN
                INSERT (product_id, sales, region, date)
                VALUES (S.product_id, S.sales, S.region, S.date);
        """
        query_job = client.query(merge_query)
        query_job.result() # Wait for the job to complete
        print(f"Data successfully merged from staging to final table: {final_table_id}")

    except Exception as e:
        print(f"An error occurred during data processing or merging: {e}")
        raise # Re-raise the exception to fail the Airflow task
    finally:
        # 3. Clean up the temporary staging table
        try:
            client.delete_table(staging_table_id)
            print(f"Staging table {staging_table_id} deleted.")
        except NotFound:
            print(f"Staging table {staging_table_id} not found, likely already deleted or never created.")
        except Exception as e:
            print(f"Error deleting staging table {staging_table_id}: {e}")