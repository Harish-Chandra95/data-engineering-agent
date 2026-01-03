from google.cloud import bigquery
from google.api_core.exceptions import NotFound

# Assuming 'client' is an initialized bigquery.Client() instance
# Assuming 'query' is the INSERT query string

# Check table exists and create if missing
table_ref = client.dataset('analytics').table('customers_staging')
try:
    client.get_table(table_ref)
    print(f"Table {table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id} already exists.")
except NotFound:
    print(f"Table {table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id} not found. Creating...")
    schema = [
        bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("email", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("country", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
    ]
    table = bigquery.Table(table_ref, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="date",
    )
    client.create_table(table, exists_ok=True)
    print(f"Table {table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id} created successfully.")
except Exception as e:
    print(f"An unexpected error occurred while checking/creating table: {e}")
    raise # Re-raise the exception if it's not NotFound

client.query(query).result()