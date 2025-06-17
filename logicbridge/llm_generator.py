"""
LLM-assisted rule generation module
"""

import os
import json
import yaml
import hashlib
import requests
from typing import Dict, List, Any, Optional
from pathlib import Path

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None


class RuleGenerator:
    """Generate rules using LLM from user stories"""
    
    def __init__(self, provider: str = "openai", model: str = "gpt-4o"):
        self.provider = provider
        self.model = model
        self.client = None
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        
        if provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ValueError("OpenAI package not available. Install with: pip install openai")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable required")
            self.client = OpenAI(api_key=api_key)
        elif provider == "ollama":
            # Test Ollama connection
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                if response.status_code != 200:
                    raise ValueError(f"Ollama server not accessible at {self.ollama_url}")
            except requests.exceptions.RequestException as e:
                raise ValueError(f"Failed to connect to Ollama at {self.ollama_url}: {e}")
        elif provider == "mock":
            # Mock provider for testing - no initialization needed
            pass
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai', 'ollama', or 'mock'")
    
    def generate_from_excel(self, excel_path: str) -> Dict[str, Any]:
        """Generate rules from Excel file containing user stories"""
        try:
            import pandas as pd
            df = pd.read_excel(excel_path)
            
            # Extract user stories (assuming they're in a 'story' or 'description' column)
            stories = []
            for col in ['story', 'description', 'requirement', 'scenario']:
                if col in df.columns:
                    stories.extend(df[col].dropna().tolist())
                    break
            
            if not stories:
                raise ValueError("No user stories found in Excel file")
            
            return self.generate_from_stories(stories)
            
        except ImportError:
            raise ValueError("pandas and openpyxl required for Excel processing. Install with: pip install pandas openpyxl")
    
    def generate_from_stories(self, stories: List[str]) -> Dict[str, Any]:
        """Generate rules from a list of user stories"""
        all_rules = []
        
        for i, story in enumerate(stories):
            try:
                rules = self._generate_rules_for_story(story, f"story_{i+1}")
                all_rules.extend(rules)
            except Exception as e:
                print(f"Warning: Failed to generate rules for story {i+1}: {e}")
                continue
        
        return {
            "rules": all_rules,
            "version": "1.0",
            "metadata": {
                "generated_by": "logicbridge_llm",
                "model": self.model,
                "story_count": len(stories)
            }
        }
    
    def _generate_rules_for_story(self, story: str, story_id: str) -> List[Dict[str, Any]]:
        """Generate rules for a single user story"""
        prompt = self._build_prompt(story)
        
        if self.provider == "openai":
            return self._generate_with_openai(prompt, story_id)
        elif self.provider == "ollama":
            return self._generate_with_ollama(prompt, story_id)
        else:
            # Mock generation for testing
            return self._generate_mock_rules(story, story_id)
    
    def _generate_with_openai(self, prompt: str, story_id: str) -> List[Dict[str, Any]]:
        """Generate rules using OpenAI API"""
        if not self.client:
            raise ValueError("OpenAI client not initialized")
            
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert business analyst who converts user stories into deterministic business rules. "
                        + "Generate rules in the LogicBridge DSL format. "
                        + "Respond with valid JSON containing an array of rules."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1  # Low temperature for deterministic output
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
                
            result = json.loads(content)
            return self._process_generated_rules(result.get("rules", []), prompt, story_id)
            
        except Exception as e:
            raise ValueError(f"OpenAI generation failed: {e}")
    
    def _generate_with_ollama(self, prompt: str, story_id: str) -> List[Dict[str, Any]]:
        """Generate rules using Ollama API"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )
            
            if response.status_code != 200:
                raise ValueError(f"Ollama API error: {response.status_code}")
            
            result_text = response.json().get("response", "")
            result = json.loads(result_text)
            return self._process_generated_rules(result.get("rules", []), prompt, story_id)
            
        except Exception as e:
            raise ValueError(f"Ollama generation failed: {e}")
    
    def _generate_mock_rules(self, story: str, story_id: str) -> List[Dict[str, Any]]:
        """Generate mock rules for testing when no LLM is available"""
        # Extract key concepts from the story
        story_lower = story.lower()
        
        rules = []
        
        # Common business rule patterns based on story content
        if "discount" in story_lower or "promotion" in story_lower:
            rules.append({
                "id": f"{story_id}_discount_rule",
                "description": f"Discount rule derived from: {story[:50]}...",
                "severity": "medium",
                "tags": ["discount", "promotion", "mock"],
                "when": {
                    "type": "greater_than",
                    "field": "order_total",
                    "value": 100
                },
                "then": {
                    "outcome": {
                        "decision": "approve_discount",
                        "discount_percent": 10,
                        "reason": "Mock discount rule"
                    }
                }
            })
        
        if "premium" in story_lower or "vip" in story_lower:
            rules.append({
                "id": f"{story_id}_premium_rule",
                "description": f"Premium customer rule derived from: {story[:50]}...",
                "severity": "high",
                "tags": ["premium", "customer", "mock"],
                "when": {
                    "type": "equals",
                    "field": "customer_tier",
                    "value": "premium"
                },
                "then": {
                    "outcome": {
                        "decision": "approve",
                        "priority": "high",
                        "reason": "Premium customer benefits"
                    }
                }
            })
        
        if "risk" in story_lower or "fraud" in story_lower:
            rules.append({
                "id": f"{story_id}_risk_rule",
                "description": f"Risk assessment rule derived from: {story[:50]}...",
                "severity": "high",
                "tags": ["risk", "fraud", "security", "mock"],
                "when": {
                    "type": "or",
                    "conditions": [
                        {
                            "type": "greater_than",
                            "field": "transaction_amount",
                            "value": 10000
                        },
                        {
                            "type": "equals",
                            "field": "risk_score",
                            "value": "high"
                        }
                    ]
                },
                "then": {
                    "outcome": {
                        "decision": "review_required",
                        "escalation": "fraud_team",
                        "reason": "High risk transaction detected"
                    }
                }
            })
        
        # Default rule if no patterns match
        if not rules:
            rules.append({
                "id": f"{story_id}_default_rule",
                "description": f"Generic rule derived from: {story[:50]}...",
                "severity": "low",
                "tags": ["generic", "mock"],
                "when": {
                    "type": "equals",
                    "field": "status",
                    "value": "active"
                },
                "then": {
                    "outcome": {
                        "decision": "approve",
                        "reason": "Default approval for active status"
                    }
                }
            })
        
        # Add metadata
        prompt_sha = hashlib.sha256(story.encode()).hexdigest()
        for rule in rules:
            rule["generated_by_llm"] = True
            rule["prompt_sha"] = prompt_sha
            rule["llm_model"] = "mock_generator"
            rule["source_story"] = story_id
        
        return rules
    
    def _process_generated_rules(self, rules: List[Dict[str, Any]], prompt: str, story_id: str) -> List[Dict[str, Any]]:
        """Process and add metadata to generated rules"""
        prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
        
        for rule in rules:
            rule["generated_by_llm"] = True
            rule["prompt_sha"] = prompt_sha
            rule["llm_model"] = self.model
            rule["source_story"] = story_id
            
            # Ensure required fields
            if "id" not in rule:
                rule["id"] = f"{story_id}_rule_{rules.index(rule)}"
            if "tags" not in rule:
                rule["tags"] = ["generated", "llm"]
        
        return rules
    
    def _build_prompt(self, story: str) -> str:
        """Build the prompt for rule generation"""
        return f"""
Convert the following user story into one or more business rules using the LogicBridge DSL format.

User Story:
{story}

Generate rules in this JSON format:
{{
  "rules": [
    {{
      "id": "unique_rule_id",
      "description": "Human readable description",
      "severity": "high|medium|low",
      "tags": ["category1", "category2"],
      "when": {{
        "type": "condition_type",
        "field": "field_name",
        "value": "expected_value"
      }},
      "then": {{
        "outcome": {{
          "decision": "approve|reject|review",
          "reason": "explanation"
        }}
      }}
    }}
  ]
}}

Supported condition types:
- "equals": exact match
- "greater_than": numeric comparison  
- "less_than": numeric comparison
- "contains": string contains
- "in": value in list
- "and": combine conditions with AND logic
- "or": combine conditions with OR logic
- "not": negate condition

Rules must be:
1. Deterministic (no randomness)
2. Purely declarative (no loops or network calls)
3. Based on the input data only
4. Have clear outcomes

Focus on extracting the core business logic and decision criteria from the story.
"""

    def validate_generated_rules(self, rules: Dict[str, Any]) -> List[str]:
        """Validate generated rules and return list of issues"""
        issues = []
        
        if "rules" not in rules:
            issues.append("Missing 'rules' field")
            return issues
        
        for i, rule in enumerate(rules["rules"]):
            rule_id = rule.get("id", f"rule_{i}")
            
            # Check required fields
            required_fields = ["id", "when", "then"]
            for field in required_fields:
                if field not in rule:
                    issues.append(f"Rule {rule_id}: missing required field '{field}'")
            
            # Validate condition structure
            if "when" in rule:
                when_issues = self._validate_condition(rule["when"], rule_id)
                issues.extend(when_issues)
            
            # Validate action structure
            if "then" in rule and "outcome" not in rule["then"]:
                issues.append(f"Rule {rule_id}: 'then' must have 'outcome' field")
        
        return issues
    
    def _validate_condition(self, condition: Dict[str, Any], rule_id: str) -> List[str]:
        """Validate a condition structure"""
        issues = []
        
        if "type" not in condition:
            issues.append(f"Rule {rule_id}: condition missing 'type' field")
            return issues
        
        condition_type = condition["type"]
        
        if condition_type in ["equals", "greater_than", "less_than", "contains"]:
            if "field" not in condition:
                issues.append(f"Rule {rule_id}: condition type '{condition_type}' requires 'field'")
            if "value" not in condition:
                issues.append(f"Rule {rule_id}: condition type '{condition_type}' requires 'value'")
        
        elif condition_type == "in":
            if "field" not in condition:
                issues.append(f"Rule {rule_id}: condition type 'in' requires 'field'")
            if "values" not in condition:
                issues.append(f"Rule {rule_id}: condition type 'in' requires 'values'")
        
        elif condition_type in ["and", "or"]:
            if "conditions" not in condition:
                issues.append(f"Rule {rule_id}: condition type '{condition_type}' requires 'conditions'")
            else:
                for sub_condition in condition.get("conditions", []):
                    sub_issues = self._validate_condition(sub_condition, rule_id)
                    issues.extend(sub_issues)
        
        elif condition_type == "not":
            if "condition" not in condition:
                issues.append(f"Rule {rule_id}: condition type 'not' requires 'condition'")
            else:
                sub_issues = self._validate_condition(condition["condition"], rule_id)
                issues.extend(sub_issues)
        
        else:
            issues.append(f"Rule {rule_id}: unknown condition type '{condition_type}'")
        
        return issues
