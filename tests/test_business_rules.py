"""
Comprehensive business rule testing for LogicBridge
Tests real-world business scenarios with various rule patterns
"""

import json
import yaml
from logicbridge.core import RuleEngine, Decision
from logicbridge.llm_generator import RuleGenerator


class TestECommerceRules:
    """Test e-commerce business rules"""
    
    def setup_method(self):
        """Set up test environment with e-commerce rules"""
        self.engine = RuleEngine()
        
        # E-commerce discount rules
        self.ecommerce_rules = {
            "rules": [
                {
                    "id": "premium_customer_discount",
                    "description": "Premium customers get 15% discount on orders over $200",
                    "severity": "high",
                    "tags": ["discount", "premium", "customer"],
                    "when": {
                        "type": "and",
                        "conditions": [
                            {
                                "type": "equals",
                                "field": "customer_tier",
                                "value": "premium"
                            },
                            {
                                "type": "greater_than",
                                "field": "order_total",
                                "value": 200
                            }
                        ]
                    },
                    "then": {
                        "outcome": {
                            "decision": "approve_discount",
                            "discount_percent": 15,
                            "reason": "Premium customer high-value order"
                        }
                    }
                },
                {
                    "id": "bulk_order_discount",
                    "description": "Orders with 20+ items get 8% discount",
                    "severity": "medium",
                    "tags": ["discount", "bulk", "quantity"],
                    "when": {
                        "type": "greater_than",
                        "field": "item_count",
                        "value": 20
                    },
                    "then": {
                        "outcome": {
                            "decision": "approve_discount",
                            "discount_percent": 8,
                            "reason": "Bulk order quantity discount"
                        }
                    }
                },
                {
                    "id": "loyalty_member_discount",
                    "description": "Loyalty members with 5+ years get special treatment",
                    "severity": "medium",
                    "tags": ["loyalty", "member", "years"],
                    "when": {
                        "type": "and",
                        "conditions": [
                            {
                                "type": "equals",
                                "field": "is_loyalty_member",
                                "value": True
                            },
                            {
                                "type": "greater_than",
                                "field": "member_years",
                                "value": 5
                            }
                        ]
                    },
                    "then": {
                        "outcome": {
                            "decision": "approve_loyalty_benefits",
                            "free_shipping": True,
                            "priority_support": True,
                            "reason": "Long-term loyalty member"
                        }
                    }
                }
            ],
            "version": "1.0",
            "metadata": {
                "domain": "ecommerce",
                "test_suite": "comprehensive_business_rules"
            }
        }
        
        self.engine.load_ruleset_from_yaml(yaml.dump(self.ecommerce_rules))
    
    def test_premium_customer_high_value_order(self):
        """Test premium customer with qualifying high-value order"""
        payload = {
            "customer_tier": "premium",
            "order_total": 350.00,
            "item_count": 5,
            "customer_id": "PREM_001"
        }
        
        decision = self.engine.evaluate(payload)
        assert decision is not None
        assert decision.rule_id == "premium_customer_discount"
        assert decision.outcome["decision"] == "approve_discount"
        assert decision.outcome["discount_percent"] == 15
        assert "premium customer" in decision.outcome["reason"].lower()
    
    def test_bulk_order_scenario(self):
        """Test bulk order discount scenario"""
        payload = {
            "customer_tier": "standard",
            "order_total": 150.00,
            "item_count": 25,
            "customer_id": "STD_002"
        }
        
        decision = self.engine.evaluate(payload)
        assert decision is not None
        assert decision.rule_id == "bulk_order_discount"
        assert decision.outcome["decision"] == "approve_discount"
        assert decision.outcome["discount_percent"] == 8
    
    def test_loyalty_member_benefits(self):
        """Test long-term loyalty member benefits"""
        payload = {
            "customer_tier": "standard",
            "order_total": 100.00,
            "item_count": 3,
            "is_loyalty_member": True,
            "member_years": 7,
            "customer_id": "LOY_003"
        }
        
        decision = self.engine.evaluate(payload)
        assert decision is not None
        assert decision.rule_id == "loyalty_member_discount"
        assert decision.outcome["decision"] == "approve_loyalty_benefits"
        assert decision.outcome["free_shipping"] is True
        assert decision.outcome["priority_support"] is True
    
    def test_no_discount_standard_customer(self):
        """Test standard customer with no qualifying discounts"""
        payload = {
            "customer_tier": "standard",
            "order_total": 50.00,
            "item_count": 2,
            "is_loyalty_member": False,
            "customer_id": "STD_004"
        }
        
        decision = self.engine.evaluate(payload)
        assert decision is None


class TestFinancialRiskRules:
    """Test financial risk assessment rules"""
    
    def setup_method(self):
        """Set up financial risk assessment rules"""
        self.engine = RuleEngine()
        
        self.risk_rules = {
            "rules": [
                {
                    "id": "high_value_transaction_review",
                    "description": "Transactions over $10,000 require manual review",
                    "severity": "high",
                    "tags": ["risk", "high_value", "review"],
                    "when": {
                        "type": "greater_than",
                        "field": "transaction_amount",
                        "value": 10000
                    },
                    "then": {
                        "outcome": {
                            "decision": "require_manual_review",
                            "escalation_level": "tier_2",
                            "max_processing_hours": 48,
                            "reason": "High-value transaction threshold exceeded"
                        }
                    }
                },
                {
                    "id": "suspicious_pattern_detection",
                    "description": "Multiple transactions from new location with high risk score",
                    "severity": "critical",
                    "tags": ["fraud", "pattern", "location"],
                    "when": {
                        "type": "and",
                        "conditions": [
                            {
                                "type": "equals",
                                "field": "is_new_location",
                                "value": True
                            },
                            {
                                "type": "greater_than",
                                "field": "risk_score",
                                "value": 80
                            },
                            {
                                "type": "greater_than",
                                "field": "daily_transaction_count",
                                "value": 5
                            }
                        ]
                    },
                    "then": {
                        "outcome": {
                            "decision": "block_transaction",
                            "require_verification": True,
                            "notify_fraud_team": True,
                            "reason": "Suspicious transaction pattern detected"
                        }
                    }
                }
            ],
            "version": "1.0",
            "metadata": {
                "domain": "financial_risk",
                "compliance": "AML_KYC"
            }
        }
        
        self.engine.load_ruleset_from_yaml(yaml.dump(self.risk_rules))


class TestRuleGenerationPatterns:
    """Test rule generation for common business patterns"""
    
    def test_generation_for_discount_scenarios(self):
        """Test rule generation for discount business scenarios"""
        generator = RuleGenerator(provider="mock", model="test")
        
        story = "Premium customers should get a 15% discount on orders over $200"
        rules = generator.generate_from_stories([story])
        
        assert "rules" in rules
        assert len(rules["rules"]) > 0
        
        rule = rules["rules"][0]
        assert rule["generated_by_llm"] is True
        assert rule["llm_model"] == "mock_generator"
        assert "discount" in rule["tags"]
        assert rule["when"]["type"] == "greater_than"
        assert rule["when"]["field"] == "order_total"
        assert rule["then"]["outcome"]["decision"] == "approve_discount"


def run_comprehensive_tests():
    """Run all comprehensive business rule tests"""
    
    # Test E-commerce Rules
    ecommerce_test = TestECommerceRules()
    ecommerce_test.setup_method()
    
    print("Testing E-commerce Rules:")
    ecommerce_test.test_premium_customer_high_value_order()
    print("✓ Premium customer discount test passed")
    
    ecommerce_test.test_bulk_order_scenario()
    print("✓ Bulk order discount test passed")
    
    ecommerce_test.test_loyalty_member_benefits()
    print("✓ Loyalty member benefits test passed")
    
    ecommerce_test.test_no_discount_standard_customer()
    print("✓ No discount standard customer test passed")
    
    # Test Financial Risk Rules
    risk_test = TestFinancialRiskRules()
    risk_test.setup_method()
    
    print("\nTesting Financial Risk Rules:")
    # Additional risk testing can be added here
    
    # Test Rule Generation
    generation_test = TestRuleGenerationPatterns()
    generation_test.test_generation_for_discount_scenarios()
    print("✓ Rule generation test passed")
    
    print("\nAll comprehensive business rule tests completed successfully!")


if __name__ == "__main__":
    run_comprehensive_tests()