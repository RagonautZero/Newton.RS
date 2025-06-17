"""
Core Python wrapper for LogicBridge rule engine
"""

import json
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Use pure Python implementation for now
class PyRuleEngine:
    def __init__(self):
        self.rules = []
        self.ruleset_sha = None
        
    def load_ruleset_from_yaml(self, yaml_content: str):
        try:
            ruleset = yaml.safe_load(yaml_content)
            self.rules = ruleset.get('rules', [])
            self._calculate_sha(yaml_content)
        except Exception as e:
            raise ValueError(f"Failed to parse YAML: {e}")
        
    def load_ruleset_from_json(self, json_content: str):
        try:
            ruleset = json.loads(json_content)
            self.rules = ruleset.get('rules', [])
            self._calculate_sha(json_content)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON: {e}")
    
    def _calculate_sha(self, content: str):
        import hashlib
        self.ruleset_sha = hashlib.sha256(content.encode()).hexdigest()
        
    def evaluate(self, payload: Dict[str, Any]) -> Optional['PyDecision']:
        import time
        start_time = time.time()
        
        for rule in self.rules:
            if self._evaluate_condition(rule.get('when', {}), payload):
                elapsed_us = int((time.time() - start_time) * 1_000_000)
                return PyDecision(
                    rule_id=rule['id'],
                    outcome=rule.get('then', {}).get('outcome', {}),
                    matched_conditions=[rule['id']],
                    elapsed_us=elapsed_us,
                    timestamp=int(time.time()),
                    rule_sha=self.ruleset_sha or "unknown"
                )
        return None
    
    def evaluate_many(self, events: List[Dict[str, Any]]) -> List[Optional['PyDecision']]:
        return [self.evaluate(event) for event in events]
        
    def get_ruleset_sha(self) -> Optional[str]:
        return self.ruleset_sha
        
    def _evaluate_condition(self, condition: Dict, payload: Dict) -> bool:
        condition_type = condition.get('type')
        
        if condition_type == 'equals':
            field = condition.get('field')
            value = condition.get('value')
            return payload.get(field) == value
            
        elif condition_type == 'greater_than':
            field = condition.get('field')
            value = condition.get('value')
            payload_value = payload.get(field)
            if isinstance(payload_value, (int, float)) and isinstance(value, (int, float)):
                return payload_value > value
            return False
            
        elif condition_type == 'less_than':
            field = condition.get('field')
            value = condition.get('value')
            payload_value = payload.get(field)
            if isinstance(payload_value, (int, float)) and isinstance(value, (int, float)):
                return payload_value < value
            return False
            
        elif condition_type == 'contains':
            field = condition.get('field')
            value = condition.get('value')
            payload_value = payload.get(field)
            if isinstance(payload_value, str) and isinstance(value, str):
                return value in payload_value
            return False
            
        elif condition_type == 'in':
            field = condition.get('field')
            values = condition.get('values', [])
            return payload.get(field) in values
            
        elif condition_type == 'and':
            conditions = condition.get('conditions', [])
            return all(self._evaluate_condition(cond, payload) for cond in conditions)
            
        elif condition_type == 'or':
            conditions = condition.get('conditions', [])
            return any(self._evaluate_condition(cond, payload) for cond in conditions)
            
        elif condition_type == 'not':
            inner_condition = condition.get('condition', {})
            return not self._evaluate_condition(inner_condition, payload)
            
        return False

class PyDecision:
    def __init__(self, rule_id, outcome, matched_conditions, elapsed_us, timestamp, rule_sha):
        self.rule_id = rule_id
        self.outcome = outcome
        self.matched_conditions = matched_conditions
        self.elapsed_us = elapsed_us
        self.timestamp = timestamp
        self.rule_sha = rule_sha


class RuleValidationError(Exception):
    """Raised when rule validation fails"""
    pass


class ExecutionError(Exception):
    """Raised when rule execution fails"""
    pass


@dataclass
class Decision:
    """Decision result from rule evaluation"""
    rule_id: str
    outcome: Dict[str, Any]
    matched_conditions: List[str]
    elapsed_us: int
    timestamp: int
    rule_sha: str
    
    @classmethod
    def from_py_decision(cls, py_decision: PyDecision) -> 'Decision':
        return cls(
            rule_id=py_decision.rule_id,
            outcome=py_decision.outcome,
            matched_conditions=py_decision.matched_conditions,
            elapsed_us=py_decision.elapsed_us,
            timestamp=py_decision.timestamp,
            rule_sha=py_decision.rule_sha
        )


class RuleEngine:
    """Python wrapper for the Rust rule engine"""
    
    def __init__(self):
        self._engine = PyRuleEngine()
    
    def load_ruleset_from_file(self, file_path: str) -> None:
        """Load ruleset from YAML or JSON file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            if file_path.endswith(('.yml', '.yaml')):
                self._engine.load_ruleset_from_yaml(content)
            elif file_path.endswith('.json'):
                self._engine.load_ruleset_from_json(content)
            else:
                raise RuleValidationError(f"Unsupported file format: {file_path}")
                
        except Exception as e:
            raise RuleValidationError(f"Failed to load ruleset: {e}")
    
    def load_ruleset_from_yaml(self, yaml_content: str) -> None:
        """Load ruleset from YAML string"""
        try:
            self._engine.load_ruleset_from_yaml(yaml_content)
        except Exception as e:
            raise RuleValidationError(f"Failed to load YAML ruleset: {e}")
    
    def load_ruleset_from_json(self, json_content: str) -> None:
        """Load ruleset from JSON string"""
        try:
            self._engine.load_ruleset_from_json(json_content)
        except Exception as e:
            raise RuleValidationError(f"Failed to load JSON ruleset: {e}")
    
    def evaluate(self, payload: Dict[str, Any]) -> Optional[Decision]:
        """Evaluate payload against loaded rules"""
        try:
            py_decision = self._engine.evaluate(payload)
            return Decision.from_py_decision(py_decision) if py_decision else None
        except Exception as e:
            raise ExecutionError(f"Rule evaluation failed: {e}")
    
    def evaluate_many(self, events: List[Dict[str, Any]]) -> List[Optional[Decision]]:
        """Evaluate multiple events in batch"""
        try:
            py_decisions = self._engine.evaluate_many(events)
            return [
                Decision.from_py_decision(d) if d else None 
                for d in py_decisions
            ]
        except Exception as e:
            raise ExecutionError(f"Batch evaluation failed: {e}")
    
    def get_ruleset_sha(self) -> Optional[str]:
        """Get SHA hash of current ruleset"""
        return self._engine.get_ruleset_sha()
