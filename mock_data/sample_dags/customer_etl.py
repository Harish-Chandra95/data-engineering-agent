from airflow.operators.python import PythonOperator

def _create_customers_staging_table_if_not_exists():
    """
    Ensures the 'analytics.customers_staging' table exists in BigQuery.
    Creates it with the expected schema and partitioning if it does not.
    """
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound
    import logging

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

    # It's good practice to explicitly define project_id if not relying on default credentials
    # project_id = "your-gcp-project-id"
    # client = bigquery.Client(project=project_id)
    client = bigquery.Client()
    
    dataset_id = "analytics"
    table_name = "customers_staging"
    table_id = f"{client.project}.{dataset_id}.{table_name}"

    table_ref = client.dataset(dataset_id).table(table_name)

    try:
        client.get_table(table_ref)
        log.info(f"BigQuery table {table_id} already exists.")
    except NotFound:
        log.info(f"BigQuery table {table_id} not found. Creating it...")
        schema = [
            bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("email", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        ]
        table = bigquery.Table(table_ref, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="date",
        )
        table = client.create_table(table)
        log.info(f"BigQuery table {table.project}.{table.dataset_id}.{table.table_id} created successfully.")
    except Exception as e:
        log.error(f"Error checking or creating table {table_id}: {e}")
        raise # Re-raise to fail the task

# Add this task within your DAG definition, for example:
# with DAG(
#     dag_id="customer_etl_pipeline",
#     start_date=days_ago(1),
#     schedule_interval=None,
#     catchup=False,
#     tags=["customer", "etl"],
# ) as dag:
#     ...
#     create_customers_staging_table = PythonOperator(
#         task_id="create_customers_staging_table",
#         python_callable=_create_customers_staging_table_if_not_exists,
#     )
#     # Ensure this task runs before any task that inserts data into analytics.customers_staging
#     # For example: create_customers_staging_table >> insert_data_into_staging_task