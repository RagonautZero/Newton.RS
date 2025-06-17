"""
Rule validation and schema checking module
"""

import json
import yaml
from typing import Dict, Any
from pathlib import Path

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


def load_schema() -> Dict[str, Any]:
    """Load the JSON schema for rule validation"""
    schema_path = Path(__file__).parent.parent / "schemas" / "rulefile-v1.json"
    
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback inline schema if file not found
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "LogicBridge Ruleset Schema",
            "type": "object",
            "required": ["rules", "version"],
            "properties": {
                "rules": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "when", "then"],
                        "properties": {
                            "id": {"type": "string"},
                            "description": {"type": "string"},
                            "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "when": {"$ref": "#/definitions/condition"},
                            "then": {
                                "type": "object",
                                "required": ["outcome"],
                                "properties": {
                                    "outcome": {"type": "object"}
                                }
                            },
                            "generated_by_llm": {"type": "boolean"},
                            "prompt_sha": {"type": "string"}
                        }
                    }
                },
                "version": {"type": "string"},
                "metadata": {"type": "object"}
            },
            "definitions": {
                "condition": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["and", "or", "not", "equals", "greater_than", "less_than", "contains", "in"]
                        }
                    },
                    "oneOf": [
                        {
                            "properties": {
                                "type": {"const": "and"},
                                "conditions": {
                                    "type": "array",
                                    "items": {"$ref": "#/definitions/condition"}
                                }
                            },
                            "required": ["conditions"]
                        },
                        {
                            "properties": {
                                "type": {"const": "or"},
                                "conditions": {
                                    "type": "array",
                                    "items": {"$ref": "#/definitions/condition"}
                                }
                            },
                            "required": ["conditions"]
                        },
                        {
                            "properties": {
                                "type": {"const": "not"},
                                "condition": {"$ref": "#/definitions/condition"}
                            },
                            "required": ["condition"]
                        },
                        {
                            "properties": {
                                "type": {"const": "equals"},
                                "field": {"type": "string"},
                                "value": {}
                            },
                            "required": ["field", "value"]
                        },
                        {
                            "properties": {
                                "type": {"const": "greater_than"},
                                "field": {"type": "string"},
                                "value": {"type": "number"}
                            },
                            "required": ["field", "value"]
                        },
                        {
                            "properties": {
                                "type": {"const": "less_than"},
                                "field": {"type": "string"},
                                "value": {"type": "number"}
                            },
                            "required": ["field", "value"]
                        },
                        {
                            "properties": {
                                "type": {"const": "contains"},
                                "field": {"type": "string"},
                                "value": {"type": "string"}
                            },
                            "required": ["field", "value"]
                        },
                        {
                            "properties": {
                                "type": {"const": "in"},
                                "field": {"type": "string"},
                                "values": {"type": "array"}
                            },
                            "required": ["field", "values"]
                        }
                    ]
                }
            }
        }


def validate_ruleset_schema(content: str, format: str = "yaml") -> None:
    """Validate ruleset against JSON schema"""
    if not JSONSCHEMA_AVAILABLE:
        # Basic validation without jsonschema
        try:
            if format == "yaml":
                data = yaml.safe_load(content)
            else:
                data = json.loads(content)
            
            # Basic structure validation
            if not isinstance(data, dict):
                raise ValueError("Ruleset must be a JSON object")
            if "rules" not in data:
                raise ValueError("Ruleset must contain 'rules' field")
            if not isinstance(data["rules"], list):
                raise ValueError("'rules' must be an array")
            
            # Validate each rule has required fields
            for i, rule in enumerate(data["rules"]):
                if not isinstance(rule, dict):
                    raise ValueError(f"Rule {i} must be an object")
                required_fields = ["id", "when", "then"]
                for field in required_fields:
                    if field not in rule:
                        raise ValueError(f"Rule {i} missing required field '{field}'")
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        return
    
    # Full validation with jsonschema
    schema = load_schema()
    
    try:
        if format == "yaml":
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)
        
        jsonschema.validate(data, schema)
        
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except jsonschema.ValidationError as e:
        raise ValueError(f"Schema validation failed: {e.message} at {'.'.join(str(x) for x in e.absolute_path)}")
    except jsonschema.SchemaError as e:
        raise ValueError(f"Invalid schema: {e}")


def validate_rule_safety(ruleset: Dict[str, Any]) -> None:
    """Validate that rules only use safe operations"""
    forbidden_patterns = [
        "import",
        "exec",
        "eval",
        "open",
        "file",
        "network",
        "socket",
        "subprocess",
        "os.",
        "sys.",
        "random",
        "__"
    ]
    
    content_str = json.dumps(ruleset).lower()
    
    for pattern in forbidden_patterns:
        if pattern in content_str:
            raise ValueError(f"Forbidden operation detected: {pattern}")


def validate_rule_determinism(ruleset: Dict[str, Any]) -> None:
    """Validate that rules are deterministic"""
    # Check for time-dependent functions that could make rules non-deterministic
    time_dependent_patterns = [
        "now()",
        "today()",
        "current_time",
        "datetime.now",
        "time.time"
    ]
    
    content_str = json.dumps(ruleset).lower()
    
    for pattern in time_dependent_patterns:
        if pattern in content_str:
            # Allow specific safe date functions
            if pattern in ["today()", "days_between"]:
                continue
            raise ValueError(f"Non-deterministic time function detected: {pattern}")


def validate_complete_ruleset(content: str, format: str = "yaml") -> None:
    """Run complete validation suite on a ruleset"""
    # Schema validation
    validate_ruleset_schema(content, format)
    
    # Parse for additional checks
    if format == "yaml":
        ruleset = yaml.safe_load(content)
    else:
        ruleset = json.loads(content)
    
    # Safety validation
    validate_rule_safety(ruleset)
    
    # Determinism validation
    validate_rule_determinism(ruleset)
