"""
Balanced Analyzer - Methodical, evidence-based, accurate classification
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


class BalancedAnalyzer:
    """Balanced analyst - systematic, evidence-based, realistic"""
    
    def __init__(self, llm_provider: str = None):
        self.llm = LLMFactory.create_client(provider=llm_provider)
        self.context_utils = ContextUtils()
        print(f"✓ Balanced Analyzer initialized")
    
    def analyze(self, error_log: Dict) -> ErrorAnalysis:
        context = self.context_utils.get_smart_context(error_log)
        
        response = self.llm.chat(
            system_prompt=self._system_prompt(),
            user_prompt=self._create_prompt(error_log, context),
            temperature=0.35,
            response_format='json'
        )
        
        data = json.loads(response.content)
        data['dag_id'] = data.get('dag_id') or error_log.get('dag_id', '')
        data['task_id'] = data.get('task_id') or error_log.get('task_id', '')
        
        if isinstance(data.get('proposed_solution'), dict):
            data['proposed_solution'] = json.dumps(data['proposed_solution'], indent=2)
        
        analysis = ErrorAnalysis(**data)
        
        if not analysis.affected_tables:
            analysis.affected_tables = self._extract_tables(error_log)
        if not analysis.relevant_files:
            analysis.relevant_files = self._extract_files(error_log)
        
        return analysis
    
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
        return """You are a methodical data engineer who analyzes errors systematically using available evidence.

CLASSIFICATION DECISION TREE (follow this order):

Step 1: Check error message for EXPLICIT keywords (highest priority)
- Contains "concurrent update" OR "serialize access" OR "lock" → concurrent_update
- Contains "table not found" OR "404" OR "does not exist" → data_issue
- Contains "ssh" OR "sftp" OR "connection refused" OR "connection timeout" → network_issue
- Contains "timeout" OR "exceeded" (but NOT connection) → timeout_issue
- Contains "worker" OR "celery" → infrastructure
- Contains "KeyError" OR "column" OR "unrecognized name" → code_bug
- Contains "schema" OR "type mismatch" OR "datatype" → schema_issue

Step 2: If no explicit keywords, use context and stack trace

CLASSIFICATION EXAMPLES (learn these patterns):

✓ "Concurrent update error: Could not serialize access" → concurrent_update (NOT data_issue!)
✓ "Table analytics.customers not found" → data_issue
✓ "KeyError: 'user_id'" → code_bug
✓ "SSH protocol banner error" → network_issue
✓ "Task exceeded timeout of 3600s" → timeout_issue
✓ "Worker pod-3 not responding" → infrastructure
✓ "Field price type FLOAT expected STRING" → schema_issue

ERROR TYPES DEFINED:
- concurrent_update: Transaction conflicts, serialization errors, locking (use when error explicitly mentions concurrent/serialize/lock)
- data_issue: Missing tables, missing data, data quality problems
- code_bug: Python errors (KeyError, TypeError), wrong column references, logic bugs
- network_issue: Connection failures, SFTP issues, SSH errors
- timeout_issue: Task timeouts, execution time exceeded
- infrastructure: Worker failures, resource exhaustion, Celery issues
- schema_issue: Type mismatches, schema evolution problems

FIX STRATEGIES:
- CREATE_TABLE → data_issue (missing table)
- FIX_CODE → code_bug (fix the code)
- ADD_RETRY → concurrent_update, network_issue, timeout_issue (retry logic)
- INVESTIGATE_DATA → data_issue (check data quality)
- FIX_CONNECTION → network_issue (connection config)
- INCREASE_TIMEOUT → timeout_issue (adjust timeout)
- FIX_SCHEMA → schema_issue (align schemas)
- RESTART_WORKER → infrastructure (worker issues)

CONFIDENCE CALIBRATION:
- 0.90-1.0: Error message explicitly states the issue + evidence confirms it
- 0.75-0.89: Strong circumstantial evidence
- 0.60-0.74: Reasonable inference from patterns
- 0.40-0.59: Multiple plausible causes
- Below 0.40: Insufficient information

CRITICAL: Read the error message carefully. If it says "concurrent update", classify as concurrent_update, NOT data_issue!

Return JSON:
{
    "error_type": "concurrent_update",
    "severity": "high",
    "confidence": 0.92,
    "dag_id": "sales_reporting_dag",
    "task_id": "aggregate_sales",
    "root_cause": "Multiple tasks writing to analytics.sales_daily simultaneously causing transaction serialization failure. Error message explicitly states 'concurrent update'.",
    "fix_strategy": "ADD_RETRY",
    "requires_code_fix": true,
    "requires_data_investigation": false,
    "affected_tables": ["analytics.sales_daily"],
    "relevant_files": ["mock_data/sample_dags/sales_report.py"],
    "proposed_solution": "Add retry logic with exponential backoff. In sales_report.py line 67, wrap df.to_gbq() with @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10)). Import from tenacity."
}

Follow the decision tree. Classify accurately based on error message keywords first."""
    
    def _create_prompt(self, error_log: Dict, context: Dict) -> str:
        prompt = f"""CLASSIFY THIS ERROR ACCURATELY

ERROR MESSAGE (read carefully for keywords):
{error_log.get('message')}

STACK TRACE:
{chr(10).join(error_log.get('stack_trace', []))}

ERROR CONTEXT:
{json.dumps(error_log.get('context', {}), indent=2)}
"""
        if context.get('dag_code'):
            code_lines = context['dag_code'].split('\n')[:45]
            prompt += f"\n\nDAG CODE:\n```python\n{chr(10).join(code_lines)}\n```\n"
        
        if context.get('schemas'):
            prompt += f"\n\nSCHEMAS:\n{json.dumps(context['schemas'], indent=2)}\n"
        
        if context.get('retry_config'):
            prompt += f"\n\nRETRY CONFIG:\n{json.dumps(context['retry_config'], indent=2)}\n"
        
        prompt += """

CLASSIFICATION CHECKLIST:
1. Does error message contain "concurrent" or "serialize"? → concurrent_update
2. Does it contain "table not found" or "404"? → data_issue
3. Does it contain "KeyError" or "column"? → code_bug
4. Does it contain "ssh" or "sftp"? → network_issue
5. Does it contain "timeout" or "exceeded"? → timeout_issue

Follow the decision tree. Return JSON with accurate error_type."""
        
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
                print(f"   ❌ Failed: {e}")
        return results


if __name__ == "__main__":
    print("🚀 Balanced Analyzer - Error Analysis\n")
    
    with open('mock_data/sample_airflow_logs.json', 'r') as f:
        logs = json.load(f)
    
    agent = BalancedAnalyzer()
    results = agent.batch_analyze(logs, limit=3)
    
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
