"""
Log Analyzer Agent
Analyzes Airflow error logs and classifies issues
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import ollama
from pydantic import BaseModel


class ErrorClassification(BaseModel):
    """Structured error classification"""
    error_type: str  # data_issue, code_bug, infrastructure, concurrent_update
    severity: str  # critical, high, medium, low
    confidence: float  # 0.0 to 1.0
    dag_id: str
    task_id: str
    root_cause_hypothesis: str
    requires_code_fix: bool
    requires_data_investigation: bool
    affected_tables: List[str]
    relevant_files: List[str]


class LogAnalyzerAgent:
    """Agent responsible for analyzing error logs"""
    
    def __init__(self, model: str = "llama3.2:3b", use_mock: bool = True):
        self.model = model
        self.use_mock = use_mock
        self.mock_data_path = os.getenv("MOCK_DATA_PATH", "./mock_data")
        
    def load_mock_logs(self) -> List[Dict]:
        """Load sample logs for local development"""
        log_file = f"{self.mock_data_path}/sample_airflow_logs.json"
        with open(log_file, 'r') as f:
            return json.load(f)
    
    def analyze_log(self, log_entry: Dict) -> ErrorClassification:
        """Analyze a single log entry using LLM"""
        
        # Prepare prompt for Llama
        prompt = self._create_analysis_prompt(log_entry)
        
        # Call Ollama
        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are an expert data engineer analyzing Airflow errors. Respond ONLY with valid JSON.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            format='json'  # Force JSON output
        )
        
        # Parse response
        result = json.loads(response['message']['content'])
        
        return ErrorClassification(**result)
    
    def _create_analysis_prompt(self, log_entry: Dict) -> str:
        """Create detailed prompt for log analysis"""
        return f"""
Analyze this Airflow error log and classify the issue:

**Error Log:**
- DAG ID: {log_entry['dag_id']}
- Task ID: {log_entry['task_id']}
- Timestamp: {log_entry['timestamp']}
- Error Message: {log_entry['message']}
- Stack Trace: {json.dumps(log_entry['stack_trace'], indent=2)}
- Context: {json.dumps(log_entry.get('context', {}), indent=2)}

**Your Task:**
Classify this error and provide structured analysis.

**Return JSON with this exact structure:**
{{
    "error_type": "one of: data_issue, code_bug, infrastructure, concurrent_update",
    "severity": "one of: critical, high, medium, low",
    "confidence": 0.0 to 1.0,
    "dag_id": "{log_entry['dag_id']}",
    "task_id": "{log_entry['task_id']}",
    "root_cause_hypothesis": "brief explanation of what caused this",
    "requires_code_fix": true or false,
    "requires_data_investigation": true or false,
    "affected_tables": ["list", "of", "table", "names"],
    "relevant_files": ["list", "of", "file", "paths"]
}}

**Classification Guidelines:**
- "data_issue": Missing data, schema mismatches, data quality problems
- "code_bug": Logic errors, typos, wrong column names
- "infrastructure": Resource issues, permissions, network
- "concurrent_update": Transaction conflicts, locking issues
"""
    
    def batch_analyze(self, limit: Optional[int] = None) -> List[ErrorClassification]:
        """Analyze multiple logs"""
        logs = self.load_mock_logs()
        
        if limit:
            logs = logs[:limit]
        
        results = []
        for log in logs:
            print(f"\n{'='*60}")
            print(f"Analyzing: {log['dag_id']} / {log['task_id']}")
            print(f"{'='*60}")
            
            classification = self.analyze_log(log)
            results.append(classification)
            
            print(f"\n✅ Classification Complete:")
            print(f"   Type: {classification.error_type}")
            print(f"   Severity: {classification.severity}")
            print(f"   Confidence: {classification.confidence:.2f}")
            print(f"   Hypothesis: {classification.root_cause_hypothesis}")
            
        return results


# Demo / Test
if __name__ == "__main__":
    print("🚀 Starting Log Analyzer Agent...")
    
    agent = LogAnalyzerAgent()
    results = agent.batch_analyze(limit=2)  # Analyze first 2 logs
    
    print(f"\n\n{'='*60}")
    print(f"📊 SUMMARY: Analyzed {len(results)} errors")
    print(f"{'='*60}")
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.dag_id} → {result.error_type} ({result.confidence:.0%} confidence)")