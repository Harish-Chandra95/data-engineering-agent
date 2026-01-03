"""
Conservative Analyzer - Cautious expert, considers multiple possibilities
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


class ConservativeAnalyzer:
    """Conservative expert - thorough but cautious"""
    
    def __init__(self, llm_provider: str = None):
        self.llm = LLMFactory.create_client(provider=llm_provider)
        self.context_utils = ContextUtils()
        print(f"✓ Conservative Analyzer initialized")
    
    def analyze(self, error_log: Dict) -> ErrorAnalysis:
        context = self.context_utils.get_smart_context(error_log)
        
        response = self.llm.chat(
            system_prompt=self._system_prompt(),
            user_prompt=self._create_prompt(error_log, context),
            temperature=0.5,  # Higher temp for more nuanced analysis
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
        return """You are a thoughtful data engineer who carefully considers multiple possibilities before diagnosing issues.

Your approach:
- Consider alternative explanations
- Note what information is missing
- Be honest about uncertainty
- Recommend investigation when unclear

CONFIDENCE SCORING (critical - be realistic):
- 0.95-1.0: Obvious error with clear evidence (e.g., "Table X not found" + code shows INSERT into X)
- 0.80-0.94: Strong evidence but some ambiguity
- 0.60-0.79: Likely cause but needs verification
- 0.40-0.59: Multiple possible causes, investigation needed
- 0.0-0.39: Insufficient information

EXAMPLES:
- "Table not found" with missing table in code → 0.95 confidence
- "Concurrent update" without retry config visible → 0.75 confidence (likely but unverified)
- Generic "Connection timeout" → 0.60 confidence (many possible causes)

Return JSON:
{
    "error_type": "data_issue",
    "severity": "high",
    "confidence": 0.75,
    "dag_id": "customer_etl_pipeline",
    "task_id": "load_customer_data",
    "root_cause": "Table likely doesn't exist, though could also be permissions. Need to verify table existence and service account permissions.",
    "fix_strategy": "CREATE_TABLE",
    "requires_code_fix": true,
    "requires_data_investigation": true,
    "affected_tables": ["analytics.customers_staging"],
    "relevant_files": ["mock_data/sample_dags/customer_etl.py"],
    "proposed_solution": "First verify table doesn't exist with: SELECT * FROM analytics.INFORMATION_SCHEMA.TABLES WHERE table_name='customers_staging'. If missing, create with DDL. Also check service account has dataset.table.create permission."
}

Be thoughtful and conservative with confidence scores."""
    
    def _create_prompt(self, error_log: Dict, context: Dict) -> str:
        prompt = f"""ERROR: {error_log.get('message')}

STACK TRACE:
{chr(10).join(error_log.get('stack_trace', []))}

CONTEXT: {json.dumps(error_log.get('context', {}), indent=2)}
"""
        if context.get('dag_code'):
            prompt += f"\n\nDAG CODE:\n```python\n{context['dag_code'][:1000]}\n```\n"
        if context.get('schemas'):
            prompt += f"\n\nSCHEMAS: {json.dumps(context['schemas'], indent=2)}\n"
        
        prompt += "\n\nAnalyze carefully. What are we certain about? What's ambiguous? Return JSON."
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
                print(f"✅ {analysis.error_type} | Confidence: {analysis.confidence:.0%}")
            except Exception as e:
                print(f"❌ {e}")
        return results


if __name__ == "__main__":
    print("🔍 Conservative Analyzer\n")
    
    with open('mock_data/sample_airflow_logs.json', 'r') as f:
        logs = json.load(f)
    
    agent = ConservativeAnalyzer()
    results = agent.batch_analyze(logs, limit=3)
    
    print(f"\n{'='*60}")
    print("CONSERVATIVE ANALYSIS")
    print(f"{'='*60}\n")
    
    for r in results:
        print(f"[{r.error_type.upper()}] {r.dag_id}")
        print(f"Confidence: {r.confidence:.0%} | Severity: {r.severity}")
        print(f"Root Cause: {r.root_cause}")
        print(f"Fix: {r.proposed_solution[:120]}...\n")
