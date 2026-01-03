"""
Smart context gathering - minimal, focused, fast
"""
import json
import re
from typing import Dict, List


class ContextUtils:
    """Gathers only relevant context based on error patterns"""
    
    def __init__(self, mock_data_path: str = "./mock_data"):
        self.mock_data_path = mock_data_path
        
        self.dag_files = {
            'customer_etl_pipeline': 'customer_etl.py',
            'sales_reporting_dag': 'sales_report.py',
            'ftp_file_ingestion': 'ftp_ingestion.py',
            'user_analytics_pipeline': 'user_analytics.py',
            'product_analytics': 'product_analytics.py',
            'revenue_analytics': 'revenue_analytics.py',
            'long_running_pipeline': 'long_running_pipeline.py',
            'realtime_processing': 'realtime_stream.py',
            'vendor_data_sync': 'vendor_sync.py',
        }
    
    def get_smart_context(self, error_log: Dict) -> Dict:
        """
        Intelligently gather context based on error pattern
        Returns ONLY what's needed - no bloat
        """
        msg = error_log.get('message', '').lower()
        context = {}
        
        # Always get DAG code if available
        if error_log.get('dag_id'):
            context['dag_code'] = self._read_dag(error_log['dag_id'])
        
        # Pattern-based context gathering
        if any(kw in msg for kw in ['table', 'bigquery', '404', 'not found', 'schema', 'column']):
            # Data/schema issues need schemas
            context['schemas'] = self._get_schemas(error_log)
        
        if any(kw in msg for kw in ['sftp', 'ssh', 'connection', 'timeout']):
            # Network issues need connection info
            context['connection_info'] = self._extract_connection(error_log)
        
        if 'concurrent' in msg or 'lock' in msg or 'serialize' in msg:
            # Concurrency issues need retry config
            context['retry_config'] = self._extract_retry_config(error_log)
            context['schemas'] = self._get_schemas(error_log)
        
        if 'type' in msg or 'datatype' in msg:
            # Type mismatches need specific details
            ctx = error_log.get('context', {})
            context['type_mismatch'] = {
                'field': ctx.get('field_name'),
                'expected': ctx.get('expected_type'),
                'actual': ctx.get('actual_type')
            }
        
        return context
    
    def _read_dag(self, dag_id: str) -> str:
        """Read DAG file"""
        filename = self.dag_files.get(dag_id) or f"{dag_id}.py"
        path = f"{self.mock_data_path}/sample_dags/{filename}"
        
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return f"# DAG not found: {dag_id}"
    
    def _get_schemas(self, error_log: Dict) -> Dict:
        """Get relevant BigQuery schemas"""
        tables = self._extract_tables(error_log)
        if not tables:
            return {}
        
        try:
            with open(f"{self.mock_data_path}/bigquery_schemas.json", 'r') as f:
                all_schemas = json.load(f)
                return {t: all_schemas[t] for t in tables if t in all_schemas}
        except FileNotFoundError:
            return {}
    
    def _extract_tables(self, error_log: Dict) -> List[str]:
        """Extract table names from error"""
        text = error_log.get('message', '') + str(error_log.get('context', {}))
        tables = re.findall(r'([\w-]+\.[\w-]+(?:\.[\w-]+)?)', text)
        return list(set(tables))
    
    def _extract_connection(self, error_log: Dict) -> Dict:
        """Extract connection details"""
        ctx = error_log.get('context', {})
        return {
            'host': ctx.get('sftp_host') or ctx.get('database_host'),
            'port': ctx.get('sftp_port') or ctx.get('database_port'),
            'user': ctx.get('sftp_user'),
            'timeout': ctx.get('timeout') or ctx.get('connection_timeout'),
        }
    
    def _extract_retry_config(self, error_log: Dict) -> Dict:
        """Extract retry configuration"""
        ctx = error_log.get('context', {})
        return {
            'current_retries': ctx.get('retries', 0),
            'max_retries': ctx.get('max_retries', 3),
            'concurrent_tasks': ctx.get('concurrent_task_count'),
        }
