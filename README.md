# Data Engineering Agent

Multi-agent system for analyzing Airflow errors and automatically creating fixes.

## Features
- 🔍 Log analysis with local LLM (Llama 3.2)
- 🤖 Multi-agent architecture using MCP
- 🔧 Automated remediation via GitHub PRs
- 💰 Low cost (~$6-11/month when deployed)

## Local Development
```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python agents/orchestrator.py
```

## Architecture
- Agent 1: Log Analyzer
- Agent 2: Context Gatherer
- Agent 3: Diagnostic Engine
- Agent 4: Remediation Creator
- Agent 5: Orchestrator



git remote add origin https://github.com/Harish-Chandra95/data-engineering-agent.git
