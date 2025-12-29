"""
Product Analytics DAG
Analyzes product performance
"""
from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'analytics-team',
    'retries': 0,
}

# BUG: Query references 'product_category' but actual column is 'category'
query = """
    SELECT 
        product_id,
        product_category,  -- Wrong column name!
        sales
    FROM analytics.products
    WHERE date = '2024-12-27'
"""

with DAG(
    'product_analytics',
    default_args=default_args,
    description='Product analytics pipeline',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    
    join_data = BigQueryInsertJobOperator(
        task_id='join_product_data',
        configuration={
            'query': {
                'query': query,
                'useLegacySql': False,
            }
        },
    )
