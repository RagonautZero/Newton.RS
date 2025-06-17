"""
Newton.RS - Deterministic Rule Engine with LLM Integration

A high-performance, deterministic rule engine with LLM integration for 
auditable business rule validation and generation.

License: MIT
"""

__version__ = "1.0.0"

from .core import RuleEngine, Decision, RuleValidationError, ExecutionError

__all__ = ["RuleEngine", "Decision", "RuleValidationError", "ExecutionError"]
