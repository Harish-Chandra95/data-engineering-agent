"""
Test how temperature affects analysis
"""
from models import LLMFactory
import json

# Same error, different temperatures
error_msg = "Table analytics.customers_staging not found"

print("="*60)
print("TEMPERATURE EXPERIMENT")
print("="*60)

for temp in [0.1, 0.5, 0.9]:
    print(f"\n🌡️  Temperature: {temp}")
    print("-"*60)
    
    llm = LLMFactory.create_client()
    
    response = llm.chat(
        system_prompt="You are analyzing an error. Classify it as 'data_issue' or 'code_bug'.",
        user_prompt=f"Error: {error_msg}\n\nIs this a data_issue or code_bug? Explain briefly.",
        temperature=temp,
        response_format='text'
    )
    
    print(response.content)

print("\n" + "="*60)
print("Notice: Low temp = similar responses, High temp = varied")
