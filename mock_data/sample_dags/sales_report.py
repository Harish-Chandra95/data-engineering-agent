from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

default_args = {
    'owner': 'analytics-team',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception), # Retries on any exception, including potential BigQuery concurrency errors
    reraise=True
)
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
) as dag:
    
    aggregate = PythonOperator(
        task_id='aggregate_sales',
        python_callable=aggregate_sales_data,
    )
