"""
Compare all 3 analyzer versions
"""
import json
from agents.analyzer_conservative import ConservativeAnalyzer
from agents.analyzer_aggressive import AggressiveAnalyzer
from agents.analyzer_balanced import BalancedAnalyzer

print("🔬 ANALYZER COMPARISON TEST\n")
print("="*70)

# Load test data
with open('mock_data/sample_airflow_logs.json', 'r') as f:
    logs = json.load(f)

# Test first 2 errors
test_logs = logs[:2]

# Run all 3 analyzers
print("\n1️⃣  CONSERVATIVE ANALYZER (Cautious)")
print("-"*70)
conservative = ConservativeAnalyzer()
conservative_results = conservative.batch_analyze(test_logs)

print("\n\n2️⃣  AGGRESSIVE ANALYZER (Fast & Confident)")
print("-"*70)
aggressive = AggressiveAnalyzer()
aggressive_results = aggressive.batch_analyze(test_logs)

print("\n\n3️⃣  BALANCED ANALYZER (Evidence-Based)")
print("-"*70)
balanced = BalancedAnalyzer()
balanced_results = balanced.batch_analyze(test_logs)

# Comparison
print("\n\n" + "="*70)
print("COMPARISON SUMMARY")
print("="*70)

for i, log in enumerate(test_logs):
    print(f"\n📋 Error {i+1}: {log['dag_id']} / {log['task_id']}")
    print(f"   Error: {log['message'][:80]}...")
    print(f"\n   Conservative: {conservative_results[i].confidence:.0%} confidence | {conservative_results[i].error_type}")
    print(f"   Aggressive:   {aggressive_results[i].confidence:.0%} confidence | {aggressive_results[i].error_type}")
    print(f"   Balanced:     {balanced_results[i].confidence:.0%} confidence | {balanced_results[i].error_type}")
    
    print(f"\n   Solutions:")
    print(f"   Conservative: {conservative_results[i].proposed_solution[:100]}...")
    print(f"   Aggressive:   {aggressive_results[i].proposed_solution[:100]}...")
    print(f"   Balanced:     {balanced_results[i].proposed_solution[:100]}...")

print("\n" + "="*70)
