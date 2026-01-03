"""
Analyzer Agent - Diagnoses errors with robust error handling
"""
import json
import sys
from typing import Dict, List
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from pydantic import BaseModel
from models import LLMFactory
from utils import ContextUtils
from dotenv import load_dotenv
import re

load_dotenv()


class ErrorAnalysis(BaseModel):
    error_type: str
    severity: str
    confidence: float
    dag_id: str
    task_id: str
    root_cause: str
    fix_strategy: str
    requires_code_fix: bool
    requires_data_investigation: bool
    affected_tables: List[str]
    relevant_files: List[str]
    proposed_solution: str


class AnalyzerAgent:
    """Analyzes errors and recommends fix strategies"""
    
    def __init__(self, llm_provider: str = None):
        self.llm = LLMFactory.create_client(provider=llm_provider)
        self.context_utils = ContextUtils()
        print(f"✓ Analyzer Agent initialized")
    
    def analyze(self, error_log: Dict) -> ErrorAnalysis:
        context = self.context_utils.get_smart_context(error_log)
        
        response = self.llm.chat(
            system_prompt=self._system_prompt(),
            user_prompt=self._create_prompt(error_log, context),
            temperature=0.35,
            response_format='json'
        )
        
        try:
            data = json.loads(response.content)
            
            # Ensure all required fields are present
            data['dag_id'] = data.get('dag_id') or error_log.get('dag_id', '')
            data['task_id'] = data.get('task_id') or error_log.get('task_id', '')
            
            # Critical: Ensure proposed_solution exists
            if not data.get('proposed_solution'):
                # Generate fallback based on fix_strategy
                data['proposed_solution'] = self._generate_fallback_solution(
                    data.get('fix_strategy', 'INVESTIGATE'),
                    data.get('error_type', 'unknown'),
                    error_log
                )
            
            # Convert proposed_solution if it's an object
            if isinstance(data.get('proposed_solution'), dict):
                data['proposed_solution'] = json.dumps(data['proposed_solution'], indent=2)
            
            analysis = ErrorAnalysis(**data)
            
            # Fallback extraction
            if not analysis.affected_tables:
                analysis.affected_tables = self._extract_tables(error_log)
            if not analysis.relevant_files:
                analysis.relevant_files = self._extract_files(error_log)
            
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️  JSON parse error: {e}")
            print(f"   Response: {response.content[:300]}")
            raise
        except Exception as e:
            print(f"   ⚠️  Validation error: {e}")
            print(f"   Data received: {data if 'data' in locals() else 'None'}")
            raise
    
    def _generate_fallback_solution(self, fix_strategy: str, error_type: str, error_log: Dict) -> str:
        """Generate fallback solution if LLM doesn't provide one"""
        fallback_solutions = {
            'CREATE_TABLE': "Create the missing table with appropriate schema and add table existence checks in the DAG code.",
            'FIX_CODE': "Fix the code error by correcting the column reference or logic bug identified in the stack trace.",
            'ADD_RETRY': "Add retry logic with exponential backoff to handle transient failures.",
            'INVESTIGATE_DATA': "Run diagnostic queries to investigate data quality issues.",
            'FIX_CONNECTION': "Verify connection credentials and network configuration. Add retry logic for transient connection issues.",
            'INCREASE_TIMEOUT': "Increase task timeout and optimize the processing logic for better performance.",
            'FIX_SCHEMA': "Align schema definitions to resolve type mismatch issues.",
            'RESTART_WORKER': "Restart the affected worker and investigate resource constraints."
        }
        return fallback_solutions.get(fix_strategy, "Investigate and resolve the identified issue.")
    
    def _extract_tables(self, error_log):
        msg = error_log.get('message', '') + str(error_log.get('context', {}))
        return list(set(re.findall(r'([\w-]+\.[\w-]+)', msg)))
    
    def _extract_files(self, error_log):
        files = []
        for trace in error_log.get('stack_trace', []):
            match = re.search(r"File '([^']+)'", trace)
            if match:
                files.append(match.group(1))
        return files
    
    def _system_prompt(self) -> str:
        return """You are a methodical data engineer analyzing Airflow errors.

CLASSIFICATION RULES (check in this order):
1. "concurrent update" OR "serialize" OR "lock" → concurrent_update
2. "table not found" OR "404" OR "does not exist" → data_issue
3. "ssh" OR "sftp" OR "connection refused/timeout" → network_issue
4. "timeout" OR "exceeded" (not connection) → timeout_issue
5. "worker" OR "celery" → infrastructure
6. "KeyError" OR "column" OR "unrecognized name" → code_bug
7. "schema" OR "type mismatch" OR "datatype" → schema_issue

CONFIDENCE CALIBRATION:
- 0.90-1.0: Explicit error + confirmed evidence
- 0.75-0.89: Strong circumstantial evidence
- 0.60-0.74: Reasonable inference
- 0.40-0.59: Multiple causes possible
- <0.40: Insufficient info

PROPOSED SOLUTION (MANDATORY FIELD):
Keep it concise (2-3 sentences) - describe WHAT to fix, not detailed implementation.

EXAMPLES:
✓ "Create the missing analytics.customers_staging table with appropriate schema. Add table existence check before INSERT operations."
✓ "Implement retry logic with exponential backoff to handle transient concurrent write conflicts."
✓ "Verify SFTP credentials and host configuration. Add connection retry logic with timeout handling."
✓ "Fix column reference from 'user_id' to 'id' to match actual DataFrame schema."

CRITICAL: You MUST include "proposed_solution" field in your JSON response.

Return JSON with ALL required fields:
{
    "error_type": "network_issue",
    "severity": "medium",
    "confidence": 0.85,
    "dag_id": "ftp_file_ingestion",
    "task_id": "download_customer_files",
    "root_cause": "SSH connection to ftp.vendor.com failed due to protocol banner read error. Likely network connectivity or firewall issue.",
    "fix_strategy": "FIX_CONNECTION",
    "requires_code_fix": true,
    "requires_data_investigation": false,
    "affected_tables": [],
    "relevant_files": ["mock_data/sample_dags/ftp_ingestion.py"],
    "proposed_solution": "Verify SFTP host reachability and credentials. Add connection retry logic with exponential backoff and check firewall rules for port 22 access."
}

NEVER omit the proposed_solution field."""
    
    def _create_prompt(self, error_log: Dict, context: Dict) -> str:
        prompt = f"""ANALYZE AND RECOMMEND FIX STRATEGY

ERROR: {error_log.get('message')}

STACK TRACE:
{chr(10).join(error_log.get('stack_trace', []))}

CONTEXT: {json.dumps(error_log.get('context', {}), indent=2)}
"""
        if context.get('dag_code'):
            prompt += f"\n\nDAG CODE:\n```python\n{context['dag_code'][:1200]}\n```\n"
        if context.get('schemas'):
            prompt += f"\n\nSCHEMAS: {json.dumps(context['schemas'], indent=2)}\n"
        if context.get('retry_config'):
            prompt += f"\n\nRETRY CONFIG: {json.dumps(context['retry_config'], indent=2)}\n"
        if context.get('connection_info'):
            prompt += f"\n\nCONNECTION: {json.dumps(context['connection_info'], indent=2)}\n"
        
        prompt += """

Diagnose and recommend fix strategy.
IMPORTANT: You MUST include the "proposed_solution" field (2-3 sentences describing WHAT to fix).
Return complete JSON with all required fields."""
        return prompt
    
    def batch_analyze(self, error_logs: List[Dict], limit: int = None) -> List[ErrorAnalysis]:
        if limit:
            error_logs = error_logs[:limit]
        
        results = []
        for i, log in enumerate(error_logs, 1):
            print(f"\n[{i}/{len(error_logs)}] Analyzing: {log['dag_id']} → {log['task_id']}")
            try:
                analysis = self.analyze(log)
                results.append(analysis)
                print(f"   ✅ {analysis.error_type.upper()} | {analysis.confidence:.0%} confidence")
            except Exception as e:
                print(f"   ❌ Failed: {str(e)[:100]}")
                # Continue with other logs
                continue
        return results


if __name__ == "__main__":
    print("🚀 Data Engineering Analyzer\n")
    
    with open('mock_data/sample_airflow_logs.json', 'r') as f:
        logs = json.load(f)
    
    agent = AnalyzerAgent()
    results = agent.batch_analyze(logs, limit=4)
    
    print(f"\n{'='*60}")
    print(f"INCIDENT ANALYSIS REPORT")
    print(f"{'='*60}\n")
    
    for i, r in enumerate(results, 1):
        print(f"[INCIDENT {i}] {r.dag_id} / {r.task_id}")
        print(f"├─ Type: {r.error_type.upper()}")
        print(f"├─ Severity: {r.severity.upper()}")
        print(f"├─ Confidence: {r.confidence:.0%}")
        print(f"├─ Root Cause: {r.root_cause}")
        print(f"├─ Tables: {', '.join(r.affected_tables) if r.affected_tables else 'None'}")
        print(f"├─ Files: {', '.join(r.relevant_files) if r.relevant_files else 'None'}")
        print(f"└─ Fix ({r.fix_strategy}):")
        print(f"   {r.proposed_solution}\n")
