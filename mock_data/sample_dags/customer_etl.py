from google.cloud import bigquery
from google.api_core.exceptions import NotFound

# Initialize BigQuery client
client = bigquery.Client()

# Define table reference and schema for analytics.customers_staging
table_ref = client.dataset('analytics').table('customers_staging')
schema = [
    bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("email", "STRING", mode="NULLABLE")
]

try:
    # Check if the table exists
    client.get_table(table_ref)
    print(f"Table {table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id} already exists.")
except NotFound:
    # Create table if it does not exist
    print(f"Table {table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id} not found, creating...")
    table = bigquery.Table(table_ref, schema=schema)
    client.create_table(table)
    print(f"Table {table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id} created successfully.")
except Exception as e:
    print(f"An unexpected error occurred while checking/creating table: {e}")
    raise # Re-raise the exception to fail the task if table creation fails

# Proceed with the original query after ensuring table existence
client.query(query).result()