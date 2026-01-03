"""
Agent 2: Remediation Agent
Generates actual code fixes based on analysis
"""
import json
import sys
from typing import Dict, List
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from models import LLMFactory
from utils import ContextUtils
from agents.analyzer import ErrorAnalysis
from agents.remediation_models import (
    RemediationPlan, CodeChange, DDLStatement, ConfigChange
)
from dotenv import load_dotenv

load_dotenv()


class RemediationAgent:
    """Generates code fixes and remediation plans"""
    
    def __init__(self, llm_provider: str = None):
        self.llm = LLMFactory.create_client(provider=llm_provider)
        self.context_utils = ContextUtils()
        print(f"✓ Remediation Agent initialized")
    
    def generate_fix(self, analysis: ErrorAnalysis, error_log: Dict) -> RemediationPlan:
        """Generate complete remediation plan based on analysis"""
        
        # Get additional context if needed
        context = self.context_utils.get_smart_context(error_log)
        
        # Generate fix based on strategy
        response = self.llm.chat(
            system_prompt=self._create_system_prompt(),
            user_prompt=self._create_remediation_prompt(analysis, error_log, context),
            temperature=0.2,  # Low temp for consistent code generation
            response_format='json'
        )
        
        try:
            data = json.loads(response.content)
            
            # Ensure all lists exist
            data.setdefault('code_changes', [])
            data.setdefault('ddl_statements', [])
            data.setdefault('config_changes', [])
            data.setdefault('testing_steps', [])
            
            # Set defaults for missing fields
            data.setdefault('fix_strategy', analysis.fix_strategy)
            data.setdefault('summary', 'Remediation plan generated')
            data.setdefault('estimated_impact', 'medium')
            data.setdefault('rollback_plan', 'Standard rollback procedure')
            data.setdefault('implementation_notes', 'Follow testing steps before deploying')
            
            plan = RemediationPlan(**data)
            return plan
            
        except Exception as e:
            print(f"   ⚠️  Error parsing remediation: {e}")
            # Return basic fallback plan
            return self._create_fallback_plan(analysis)
    
    def _create_fallback_plan(self, analysis: ErrorAnalysis) -> RemediationPlan:
        """Create a basic plan if LLM fails"""
        return RemediationPlan(
            fix_strategy=analysis.fix_strategy,
            summary=f"Manual intervention required for {analysis.error_type}",
            estimated_impact="medium",
            code_changes=[],
            ddl_statements=[],
            config_changes=[],
            testing_steps=["Manually review and implement fix"],
            rollback_plan="Revert changes if issues occur",
            implementation_notes=analysis.proposed_solution
        )
    
    def _create_system_prompt(self) -> str:
        """System prompt for remediation generation"""
        return """You are a senior data engineer creating production-ready code fixes.

Your job: Generate actual implementation code, not suggestions.

CRITICAL OUTPUT REQUIREMENTS:
Return valid JSON with this exact structure:
{
    "fix_strategy": "CREATE_TABLE",
    "summary": "Brief summary of the fix",
    "estimated_impact": "low|medium|high",
    "code_changes": [
        {
            "file_path": "mock_data/sample_dags/customer_etl.py",
            "change_type": "modify",
            "language": "python",
            "description": "Add table existence check",
            "original_code": "client.query(query).result()",
            "new_code": "# Check table exists\\ntable_ref = client.dataset('analytics').table('customers_staging')\\ntry:\\n    client.get_table(table_ref)\\nexcept NotFound:\\n    # Create table if missing\\n    schema = [...]\\n    table = bigquery.Table(table_ref, schema=schema)\\n    client.create_table(table)\\n\\nclient.query(query).result()",
            "line_number": 28
        }
    ],
    "ddl_statements": [
        {
            "table_name": "analytics.customers_staging",
            "statement_type": "CREATE",
            "ddl": "CREATE TABLE IF NOT EXISTS analytics.customers_staging (\\n  customer_id STRING NOT NULL,\\n  email STRING,\\n  created_at TIMESTAMP NOT NULL,\\n  country STRING,\\n  date DATE NOT NULL\\n) PARTITION BY date",
            "description": "Create missing staging table"
        }
    ],
    "config_changes": [
        {
            "config_type": "retry",
            "file_path": "mock_data/sample_dags/sales_report.py",
            "parameter": "retries",
            "old_value": "1",
            "new_value": "3",
            "description": "Increase retry count for concurrent updates"
        }
    ],
    "testing_steps": [
        "Run unit tests for modified DAG",
        "Test with sample data in dev environment",
        "Verify table creation works correctly"
    ],
    "rollback_plan": "If issues occur: 1) Revert code changes, 2) Drop test table if created",
    "implementation_notes": "Deploy during low-traffic window. Monitor first few runs."
}

FIX STRATEGY SPECIFIC GUIDELINES:

CREATE_TABLE:
- Provide complete DDL with all columns, types, constraints
- Include PARTITION BY or CLUSTER BY if appropriate
- Add code to check table existence before operations
- Include proper error handling

FIX_CODE:
- Show exact before/after code
- Include line numbers
- Add necessary imports
- Ensure proper indentation

ADD_RETRY:
- Use tenacity library for retry logic
- Show complete decorator with parameters
- Include exponential backoff
- Add proper error handling

INVESTIGATE_DATA:
- Provide diagnostic SQL queries
- Show how to log results
- Suggest data validation checks

FIX_CONNECTION:
- Show updated connection parameters
- Add retry logic
- Include timeout settings

INCREASE_TIMEOUT:
- Show old and new timeout values
- Suggest checkpoint logic if applicable

FIX_SCHEMA:
- Show schema alignment code
- Include type casting if needed
- Add validation

All code must be:
- Production-ready (not pseudocode)
- Properly formatted
- Include imports
- Handle errors
- Be copy-paste ready

Return ONLY valid JSON. No markdown, no explanations outside JSON."""
    
    def _create_remediation_prompt(
        self, 
        analysis: ErrorAnalysis, 
        error_log: Dict,
        context: Dict
    ) -> str:
        """Create prompt for generating remediation"""
        
        prompt = f"""GENERATE PRODUCTION-READY FIX

ANALYSIS SUMMARY:
- Error Type: {analysis.error_type}
- Fix Strategy: {analysis.fix_strategy}
- Root Cause: {analysis.root_cause}
- Affected Tables: {', '.join(analysis.affected_tables) if analysis.affected_tables else 'None'}
- Affected Files: {', '.join(analysis.relevant_files) if analysis.relevant_files else 'None'}
- Proposed Solution: {analysis.proposed_solution}

ORIGINAL ERROR:
{error_log.get('message')}

CONTEXT:
{json.dumps(error_log.get('context', {}), indent=2)}
"""
        
        if context.get('dag_code'):
            code_lines = context['dag_code'].split('\n')[:60]
            prompt += f"\n\nCURRENT DAG CODE:\n```python\n{chr(10).join(code_lines)}\n```\n"
        
        if context.get('schemas'):
            prompt += f"\n\nTABLE SCHEMAS:\n{json.dumps(context['schemas'], indent=2)}\n"
        
        prompt += f"""

REQUIRED: Generate complete, production-ready fix following the fix_strategy: {analysis.fix_strategy}

Include:
1. Exact code changes (with before/after)
2. DDL statements if needed (complete CREATE TABLE)
3. Configuration changes if applicable
4. Testing steps
5. Rollback plan

Return valid JSON only."""
        
        return prompt
    
    def batch_remediate(
        self, 
        analyses: List[ErrorAnalysis],
        error_logs: List[Dict]
    ) -> List[RemediationPlan]:
        """Generate fixes for multiple analyses"""
        
        results = []
        for i, (analysis, error_log) in enumerate(zip(analyses, error_logs), 1):
            print(f"\n[{i}/{len(analyses)}] Generating fix: {analysis.dag_id} → {analysis.fix_strategy}")
            
            try:
                plan = self.generate_fix(analysis, error_log)
                results.append(plan)
                print(f"   ✅ {len(plan.code_changes)} code changes, {len(plan.ddl_statements)} DDL statements")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results.append(self._create_fallback_plan(analysis))
        
        return results
    
    def save_plan_to_file(self, plan: RemediationPlan, output_dir: str = "remediation_plans"):
        """Save remediation plan to files for easy review"""
        from pathlib import Path
        import os
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Create timestamp-based filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plan_name = f"fix_{plan.fix_strategy}_{timestamp}"
        
        # Save JSON
        json_file = output_path / f"{plan_name}.json"
        with open(json_file, 'w') as f:
            json.dump(plan.model_dump(), f, indent=2)
        
        # Save human-readable markdown
        md_file = output_path / f"{plan_name}.md"
        with open(md_file, 'w') as f:
            f.write(f"# Remediation Plan: {plan.fix_strategy}\n\n")
            f.write(f"**Summary:** {plan.summary}\n\n")
            f.write(f"**Impact:** {plan.estimated_impact}\n\n")
            
            if plan.code_changes:
                f.write("## Code Changes\n\n")
                for i, change in enumerate(plan.code_changes, 1):
                    f.write(f"### {i}. {change.file_path}\n")
                    f.write(f"**Type:** {change.change_type} | **Language:** {change.language}\n\n")
                    f.write(f"{change.description}\n\n")
                    
                    if change.original_code:
                        f.write("**Before:**\n```" + change.language + "\n")
                        f.write(change.original_code)
                        f.write("\n```\n\n")
                    
                    f.write("**After:**\n```" + change.language + "\n")
                    f.write(change.new_code)
                    f.write("\n```\n\n")
            
            if plan.ddl_statements:
                f.write("## DDL Statements\n\n")
                for i, ddl in enumerate(plan.ddl_statements, 1):
                    f.write(f"### {i}. {ddl.statement_type} {ddl.table_name}\n")
                    f.write(f"{ddl.description}\n\n")
                    f.write("```sql\n")
                    f.write(ddl.ddl)
                    f.write("\n```\n\n")
            
            if plan.config_changes:
                f.write("## Configuration Changes\n\n")
                for i, cfg in enumerate(plan.config_changes, 1):
                    f.write(f"### {i}. {cfg.file_path}\n")
                    f.write(f"{cfg.description}\n\n")
                    f.write(f"- Parameter: `{cfg.parameter}`\n")
                    f.write(f"- Old Value: `{cfg.old_value}`\n")
                    f.write(f"- New Value: `{cfg.new_value}`\n\n")
            
            f.write("## Testing Steps\n\n")
            for i, step in enumerate(plan.testing_steps, 1):
                f.write(f"{i}. {step}\n")
            
            f.write(f"\n## Rollback Plan\n\n{plan.rollback_plan}\n")
            f.write(f"\n## Implementation Notes\n\n{plan.implementation_notes}\n")
        
        print(f"   💾 Saved to: {md_file}")
        return md_file


if __name__ == "__main__":
    print("🔧 Remediation Agent - Code Fix Generation\n")
    
    # Load test data
    with open('mock_data/sample_airflow_logs.json', 'r') as f:
        logs = json.load(f)
    
    # First, run analyzer
    print("Step 1: Analyzing errors...")
    from agents.analyzer import AnalyzerAgent
    
    analyzer = AnalyzerAgent()
    analyses = analyzer.batch_analyze(logs, limit=2)
    
    # Then, generate fixes
    print("\n\nStep 2: Generating fixes...")
    remediator = RemediationAgent()
    plans = remediator.batch_remediate(analyses, logs[:2])
    
    # Save plans to files
    print("\n\nStep 3: Saving plans...")
    for i, plan in enumerate(plans, 1):
        remediator.save_plan_to_file(plan)
    
    # Display results
    print(f"\n{'='*70}")
    print(f"REMEDIATION PLANS")
    print(f"{'='*70}\n")
    
    for i, (analysis, plan) in enumerate(zip(analyses, plans), 1):
        print(f"[FIX {i}] {analysis.dag_id} / {analysis.task_id}")
        print(f"├─ Strategy: {plan.fix_strategy}")
        print(f"├─ Impact: {plan.estimated_impact.upper()}")
        print(f"├─ Summary: {plan.summary}")
        print(f"│")
        
        if plan.code_changes:
            print(f"├─ CODE CHANGES ({len(plan.code_changes)}):")
            for j, change in enumerate(plan.code_changes, 1):
                print(f"│  {j}. {change.file_path}")
                print(f"│     Type: {change.change_type} | Language: {change.language}")
                print(f"│     {change.description}")
        
        if plan.ddl_statements:
            print(f"├─ DDL STATEMENTS ({len(plan.ddl_statements)}):")
            for j, ddl in enumerate(plan.ddl_statements, 1):
                print(f"│  {j}. {ddl.statement_type} {ddl.table_name}")
                print(f"│     {ddl.description}")
        
        if plan.config_changes:
            print(f"├─ CONFIG CHANGES ({len(plan.config_changes)}):")
            for j, cfg in enumerate(plan.config_changes, 1):
                print(f"│  {j}. {cfg.parameter}: {cfg.old_value} → {cfg.new_value}")
        
        print(f"│")
        print(f"├─ TESTING STEPS:")
        for j, step in enumerate(plan.testing_steps, 1):
            print(f"│  {j}. {step}")
        
        print(f"│")
        print(f"└─ ROLLBACK: {plan.rollback_plan}\n")
