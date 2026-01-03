@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type((SSHException, NoValidConnectionsError, AuthenticationException)),
    reraise=True
)
def _connect_sftp_with_retries(hostname, port, username, password, timeout):
    """Helper function to connect to SFTP with retries."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port=port, username=username, password=password, timeout=timeout)
    return ssh

def download_files(**context):
    """Download files from SFTP server"""
    
    # Connection details
    hostname = 'ftp.vendor.com'
    port = 22
    username = 'airflow_service'
    password = context['params']['sftp_password']
    
    # Implement retry logic for connection
    try:
        ssh = _connect_sftp_with_retries(hostname, port, username, password, timeout=60) # Increased timeout
        sftp = ssh.open_sftp()
        
        # Download files
        sftp.get('/incoming/customers_20241227.csv', '/data/customers.csv')
        
        sftp.close()
        ssh.close()
    except (SSHException, NoValidConnectionsError, AuthenticationException) as e:
        # Log the error and re-raise to fail the task
        print(f"Failed to connect to SFTP after multiple retries: {e}")
        raise