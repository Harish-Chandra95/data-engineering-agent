"""
Aggressive Analyzer - Fast decisions, high confidence, production-focused
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


class AggressiveAnalyzer:
    """Aggressive senior engineer - fast, confident, decisive"""
    
    def __init__(self, llm_provider: str = None):
        self.llm = LLMFactory.create_client(provider=llm_provider)
        self.context_utils = ContextUtils()
        print(f"✓ Aggressive Analyzer initialized")
    
    def analyze(self, error_log: Dict) -> ErrorAnalysis:
        context = self.context_utils.get_smart_context(error_log)
        
        response = self.llm.chat(
            system_prompt=self._system_prompt(),
            user_prompt=self._create_prompt(error_log, context),
            temperature=0.2,  # Low temp for consistent, confident analysis
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
        return """You are a battle-tested senior engineer who has seen every possible pipeline failure. You make fast, confident decisions based on pattern recognition.

Production mindset:
- Identify the issue immediately
- No overthinking - trust your experience
- Provide the fix that works 99% of the time
- Ship it

CONFIDENCE SCORING:
- 0.90-1.0: Standard errors you've fixed 100+ times
- 0.80-0.89: Common patterns, obvious solution
- 0.70-0.79: Less common but still recognizable
- Below 0.70: Rarely happens - you're always confident

Return JSON:
{
    "error_type": "data_issue",
    "severity": "critical",
    "confidence": 0.95,
    "dag_id": "customer_etl_pipeline",
    "task_id": "load_customer_data",
    "root_cause": "Table doesn't exist. Classic mistake.",
    "fix_strategy": "CREATE_TABLE",
    "requires_code_fix": true,
    "requires_data_investigation": false,
    "affected_tables": ["analytics.customers_staging"],
    "relevant_files": ["mock_data/sample_dags/customer_etl.py"],
    "proposed_solution": "CREATE TABLE analytics.customers_staging (customer_id STRING, email STRING, date DATE). Add client.create_table(table, exists_ok=True) at line 28. Done."
}

Be decisive. Production is down."""
    
    def _create_prompt(self, error_log: Dict, context: Dict) -> str:
        prompt = f"""ERROR: {error_log.get('message')}
STACK: {chr(10).join(error_log.get('stack_trace', [])[:3])}
"""
        if context.get('dag_code'):
            prompt += f"\nCODE:\n```python\n{context['dag_code'][:800]}\n```\n"
        
        prompt += "\nDiagnose and fix. Fast. JSON only."
        return prompt
    
    def batch_analyze(self, error_logs: List[Dict], limit: int = None) -> List[ErrorAnalysis]:
        if limit:
            error_logs = error_logs[:limit]
        
        results = []
        for i, log in enumerate(error_logs, 1):
            print(f"\n[{i}/{len(error_logs)}] {log['dag_id']} → {log['task_id']}")
            try:
                analysis = self.analyze(log)
                results.append(analysis)
                print(f"✅ {analysis.error_type} | {analysis.confidence:.0%} confidence")
            except Exception as e:
                print(f"❌ {e}")
        return results


if __name__ == "__main__":
    print("⚡ Aggressive Analyzer\n")
    
    with open('mock_data/sample_airflow_logs.json', 'r') as f:
        logs = json.load(f)
    
    agent = AggressiveAnalyzer()
    results = agent.batch_analyze(logs, limit=3)
    
    print(f"\n{'='*60}")
    print("AGGRESSIVE ANALYSIS")
    print(f"{'='*60}\n")
    
    for r in results:
        print(f"[{r.error_type.upper()}] {r.dag_id}")
        print(f"Confidence: {r.confidence:.0%} | Severity: {r.severity}")
        print(f"Root Cause: {r.root_cause}")
        print(f"Fix: {r.proposed_solution[:120]}...\n")
