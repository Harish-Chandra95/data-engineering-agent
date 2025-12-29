"""
FTP File Ingestion DAG
Downloads customer files from vendor SFTP server
"""
from airflow import DAG
from airflow.providers.sftp.operators.sftp import SFTPOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import paramiko

default_args = {
    'owner': 'data-integration',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def download_files(**context):
    """Download files from SFTP server"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Connection details
    hostname = 'ftp.vendor.com'
    port = 22
    username = 'airflow_service'
    password = context['params']['sftp_password']
    
    # BUG: SFTP server may be down or firewall blocking connection
    ssh.connect(hostname, port=port, username=username, password=password, timeout=30)
    sftp = ssh.open_sftp()
    
    # Download files
    sftp.get('/incoming/customers_20241227.csv', '/data/customers.csv')
    
    sftp.close()
    ssh.close()

with DAG(
    'ftp_file_ingestion',
    default_args=default_args,
    description='Download files from vendor SFTP',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    
    download = PythonOperator(
        task_id='download_customer_files',
        python_callable=download_files,
        params={'sftp_password': '{{ var.value.sftp_password }}'}
    )
