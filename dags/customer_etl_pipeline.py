from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCreateEmptyTableOperator,
    BigQueryInsertJobOperator,
)
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='customer_etl_pipeline',
    start_date=datetime(2023, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    default_args=default_args,
    tags=['customer', 'etl', 'bigquery'],
) as dag:
    # Task to ensure the analytics.customers_staging table exists
    # This resolves the '404 Table analytics.customers_staging not found' error
    create_customers_staging_table = BigQueryCreateEmptyTableOperator(
        task_id='create_customers_staging_table',
        dataset_id='analytics',
        table_id='customers_staging',
        schema_fields=[
            {"name": "customer_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "email", "type": "STRING", "mode": "NULLABLE"},
        ],
        gcp_conn_id='google_cloud_default', # Ensure this connection ID is configured in Airflow
        if_exists='ignore', # Do not fail if the table already exists
    )

    # Task to load data from raw.customers into analytics.customers_staging
    load_customers_to_staging = BigQueryInsertJobOperator(
        task_id='load_customers_to_staging',
        configuration={
            "query": {
                "query": """
                    INSERT INTO `{{ params.project_id }}.analytics.customers_staging` (customer_id, email)
                    SELECT customer_id, email
                    FROM `{{ params.project_id }}.raw.customers`;
                """,
                "useLegacySql": False,
            }
        },
        params={
            "project_id": "your-gcp-project-id" # IMPORTANT: Replace with your actual GCP project ID or use Airflow variables
        },
        gcp_conn_id='google_cloud_default',
    )

    # Define task dependencies
    create_customers_staging_table >> load_customers_to_staging
