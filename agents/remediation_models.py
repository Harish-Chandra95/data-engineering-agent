"""
Data models for remediation agent
"""
from pydantic import BaseModel
from typing import List, Dict, Optional


class CodeChange(BaseModel):
    """Represents a code modification"""
    file_path: str
    change_type: str  # "modify", "create", "delete"
    language: str  # "python", "sql", "yaml"
    description: str
    original_code: Optional[str] = None  # For modifications
    new_code: str
    line_number: Optional[int] = None  # For modifications


class DDLStatement(BaseModel):
    """Database DDL statement"""
    table_name: str
    statement_type: str  # "CREATE", "ALTER", "DROP"
    ddl: str
    description: str


class ConfigChange(BaseModel):
    """Configuration changes"""
    config_type: str  # "timeout", "retry", "connection"
    file_path: str
    parameter: str
    old_value: Optional[str] = None
    new_value: str
    description: str


class RemediationPlan(BaseModel):
    """Complete remediation plan"""
    fix_strategy: str
    summary: str
    estimated_impact: str  # "low", "medium", "high"
    code_changes: List[CodeChange]
    ddl_statements: List[DDLStatement]
    config_changes: List[ConfigChange]
    testing_steps: List[str]
    rollback_plan: str
    implementation_notes: str
