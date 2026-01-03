"""
View detailed remediation output including actual code
"""
import json
from agents.analyzer import AnalyzerAgent
from agents.remediation import RemediationAgent

print("🔍 DETAILED REMEDIATION VIEW\n")

# Load errors
with open('mock_data/sample_airflow_logs.json', 'r') as f:
    logs = json.load(f)

# Analyze
analyzer = AnalyzerAgent()
analyses = analyzer.batch_analyze(logs, limit=2)

# Generate fixes
remediator = RemediationAgent()
plans = remediator.batch_remediate(analyses, logs[:2])

# Show detailed output
for i, (analysis, plan) in enumerate(zip(analyses, plans), 1):
    print(f"{'='*70}")
    print(f"REMEDIATION {i}: {analysis.dag_id}")
    print(f"{'='*70}\n")
    
    print(f"📋 SUMMARY")
    print(f"   Strategy: {plan.fix_strategy}")
    print(f"   Impact: {plan.estimated_impact}")
    print(f"   {plan.summary}\n")
    
    # Show actual code changes
    if plan.code_changes:
        print(f"💻 CODE CHANGES\n")
        for j, change in enumerate(plan.code_changes, 1):
            print(f"   [{j}] {change.file_path} (line {change.line_number or 'N/A'})")
            print(f"   {change.description}\n")
            
            if change.original_code:
                print(f"   BEFORE:")
                print(f"   ```{change.language}")
                for line in change.original_code.split('\n'):
                    print(f"   {line}")
                print(f"   ```\n")
            
            print(f"   AFTER:")
            print(f"   ```{change.language}")
            for line in change.new_code.split('\n'):
                print(f"   {line}")
            print(f"   ```\n")
    
    # Show DDL
    if plan.ddl_statements:
        print(f"🗄️  DDL STATEMENTS\n")
        for j, ddl in enumerate(plan.ddl_statements, 1):
            print(f"   [{j}] {ddl.statement_type} {ddl.table_name}")
            print(f"   {ddl.description}\n")
            print(f"   ```sql")
            for line in ddl.ddl.split('\n'):
                print(f"   {line}")
            print(f"   ```\n")
    
    # Show config changes
    if plan.config_changes:
        print(f"⚙️  CONFIG CHANGES\n")
        for j, cfg in enumerate(plan.config_changes, 1):
            print(f"   [{j}] {cfg.file_path}")
            print(f"   {cfg.description}")
            print(f"   {cfg.parameter}: {cfg.old_value} → {cfg.new_value}\n")
    
    print(f"✅ TESTING")
    for j, step in enumerate(plan.testing_steps, 1):
        print(f"   {j}. {step}")
    
    print(f"\n🔄 ROLLBACK")
    print(f"   {plan.rollback_plan}\n")
    
    print(f"📝 NOTES")
    print(f"   {plan.implementation_notes}\n")
