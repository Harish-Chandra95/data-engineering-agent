"""
Revenue Analytics DAG
Calculates revenue metrics
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
from google.cloud import bigquery

default_args = {
    'owner': 'analytics-team',
    'retries': 0,
}

def calculate_revenue_metrics(**context):
    """Calculate and load revenue metrics"""
    client = bigquery.Client()
    
    # Create sample data
    df = pd.DataFrame({
        'date': ['2024-12-27', '2024-12-27', '2024-12-27'],
        'product_id': [1, 2, 3],
        'price': ['29.99', '49.99', '99.99'],  # BUG: Should be float, not string
        'quantity': [100, 50, 25]
    })
    
    table_ref = 'analytics.revenue_metrics'
    
    # This will fail - schema expects FLOAT but we're sending STRING
    job = client.load_table_from_dataframe(df, table_ref)
    job.result()

with DAG(
    'revenue_analytics',
    default_args=default_args,
    description='Revenue metrics calculation',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    
    calculate = PythonOperator(
        task_id='calculate_metrics',
        python_callable=calculate_revenue_metrics,
    )
