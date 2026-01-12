from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd

default_args = {
    'owner': 'analytics-team',
    'retries': 5,                              # Increased for concurrent errors
    'retry_delay': timedelta(minutes=2),       # Wait before retry
    'retry_exponential_backoff': True,         # Exponential backoff
    'max_retry_delay': timedelta(minutes=15),  # Cap the delay
}

def aggregate_sales_data(**context):
    """Aggregate sales by product and region"""
    # Simulated data processing
    df = pd.DataFrame({
        'product_id': [1, 2, 3],
        'sales': [100, 200, 300],
        'region': ['US', 'EU', 'APAC']
    })
    
    # This might cause concurrent update issues under heavy load
    # Multiple tasks trying to write simultaneously
    df.to_gbq('analytics.sales_daily', if_exists='append')
    
with DAG(
    'sales_reporting_dag',
    default_args=default_args,
    description='Daily sales reporting',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,  # Prevent concurrent DAG runs that could cause update conflicts
) as dag:
    
    aggregate = PythonOperator(
        task_id='aggregate_sales',
        python_callable=aggregate_sales_data,
    )
