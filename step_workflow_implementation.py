#!/usr/bin/env python3
"""
Complete implementation of step-based workflows with before/after rule dependencies
Newton.RS - Deterministic Rule Engine with LLM Integration
"""

import sys
import os
sys.path.append('/home/runner/workspace')

from logicbridge.core import RuleEngine
from logicbridge.audit import AuditLogger
import yaml
import json
import time
from typing import Dict, List, Any, Optional

class StepWorkflowEngine:
    """Implements step-based rule execution with before/after dependencies"""
    
    def __init__(self):
        self.rule_engine = RuleEngine()
        self.audit_logger = AuditLogger()
        self.workflow_context = {}
        self.execution_history = []
    
    def load_step_workflow_rules(self, ruleset_path: str):
        """Load step-based workflow rules"""
        self.rule_engine.load_ruleset_from_file(ruleset_path)
    
    def execute_step_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute step-based workflow with before/after rule dependencies"""
        
        self.workflow_context = {**input_data}
        self.execution_history = []
        
        workflow_start = time.time()
        
        # Step 1: Application validation
        step1_result = self._execute_step(
            step_name="application_validation",
            rule_target="validate_loan_application",
            data=self.workflow_context
        )
        
        if not step1_result or step1_result.get("decision") != "validation_passed":
            return self._handle_early_termination("validation_failed", step1_result)
        
        # Update context with step 1 results (AFTER step 1)
        self.workflow_context.update({
            "previous_step_result": step1_result["decision"],
            "validation_score": step1_result.get("validation_score", 0)
        })
        
        # Step 2: Credit assessment (BEFORE rule: validation must pass)
        step2_result = self._execute_step(
            step_name="credit_assessment", 
            rule_target="assess_credit_risk_step",
            data=self.workflow_context,
            before_condition=lambda: self.workflow_context.get("previous_step_result") == "validation_passed"
        )
        
        if not step2_result:
            # Check alternative path: manual review
            manual_review_result = self._execute_step(
                step_name="manual_review_check",
                rule_target="manual_review_required", 
                data=self.workflow_context
            )
            if manual_review_result:
                return self._finalize_workflow(workflow_id, workflow_start, "manual_review_path")
            else:
                return self._handle_early_termination("credit_assessment_failed", None)
        
        # Update context with step 2 results (AFTER step 2)
        self.workflow_context.update({
            "previous_step_result": step2_result["decision"],
            "risk_level": step2_result.get("risk_level"),
            "interest_rate": step2_result.get("interest_rate")
        })
        
        # Step 3: Income verification (BEFORE rule: credit assessment must pass)
        step3_result = self._execute_step(
            step_name="income_verification",
            rule_target="verify_income_step",
            data=self.workflow_context,
            before_condition=lambda: self.workflow_context.get("previous_step_result") == "low_risk_approved"
        )
        
        if not step3_result or step3_result.get("decision") != "income_verified":
            return self._handle_early_termination("income_verification_failed", step3_result)
        
        # Update context with step 3 results (AFTER step 3)
        self.workflow_context.update({
            "previous_step_result": step3_result["decision"],
            "verification_status": step3_result.get("verification_status")
        })
        
        # Step 4: Final approval (BEFORE rule: income must be verified)
        step4_result = self._execute_step(
            step_name="final_approval",
            rule_target="final_loan_approval_step", 
            data=self.workflow_context,
            before_condition=lambda: self.workflow_context.get("previous_step_result") == "income_verified"
        )
        
        if not step4_result or step4_result.get("decision") != "loan_approved":
            return self._handle_early_termination("final_approval_failed", step4_result)
        
        # AFTER rule: Trigger account setup if approved
        if step4_result.get("trigger_after_rule") == "setup_loan_account":
            account_setup_result = self._execute_step(
                step_name="account_setup",
                rule_target="setup_loan_account",
                data={
                    **self.workflow_context,
                    "trigger_after_rule": "setup_loan_account"
                }
            )
            if account_setup_result:
                self.workflow_context.update(account_setup_result)
        
        return self._finalize_workflow(workflow_id, workflow_start, "successful_completion")
    
    def _execute_step(self, step_name: str, rule_target: str, data: Dict[str, Any], 
                     before_condition: Optional[callable] = None) -> Optional[Dict[str, Any]]:
        """Execute a single workflow step with optional before condition"""
        
        step_start = time.time()
        
        # Check before condition if specified
        if before_condition and not before_condition():
            self.execution_history.append({
                "step": step_name,
                "status": "skipped",
                "reason": "before_condition_not_met",
                "execution_time_ms": 0
            })
            return None
        
        try:
            # Execute rule evaluation
            decision = self.rule_engine.evaluate(data)
            
            step_time = (time.time() - step_start) * 1000
            
            if decision and decision.rule_id == rule_target:
                # Log successful step execution
                self.audit_logger.log_decision(decision)
                
                self.execution_history.append({
                    "step": step_name,
                    "rule_id": decision.rule_id,
                    "status": "completed",
                    "decision": decision.outcome,
                    "execution_time_ms": step_time
                })
                
                return decision.outcome
            else:
                self.execution_history.append({
                    "step": step_name,
                    "status": "no_match",
                    "rule_target": rule_target,
                    "execution_time_ms": step_time
                })
                return None
                
        except Exception as e:
            self.execution_history.append({
                "step": step_name,
                "status": "error", 
                "error": str(e),
                "execution_time_ms": (time.time() - step_start) * 1000
            })
            return None
    
    def _handle_early_termination(self, reason: str, last_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle workflow termination before completion"""
        
        # Check for rejection rule
        rejection_data = {
            **self.workflow_context,
            "termination_reason": reason
        }
        
        rejection_decision = self.rule_engine.evaluate(rejection_data)
        if rejection_decision and rejection_decision.rule_id == "application_rejected":
            self.audit_logger.log_decision(rejection_decision)
            final_outcome = rejection_decision.outcome
        else:
            final_outcome = {
                "decision": "workflow_terminated",
                "reason": reason,
                "last_successful_result": last_result
            }
        
        return {
            "workflow_status": "terminated",
            "termination_reason": reason,
            "final_outcome": final_outcome,
            "execution_history": self.execution_history,
            "context": self.workflow_context
        }
    
    def _finalize_workflow(self, workflow_id: str, start_time: float, completion_type: str) -> Dict[str, Any]:
        """Finalize workflow execution and return results"""
        
        total_time = (time.time() - start_time) * 1000
        
        # Log workflow completion
        self.audit_logger.log_ruleset_change(
            rule_sha=f"workflow_{workflow_id}",
            author="step_workflow_engine",
            content=f"Workflow completed: {completion_type}"
        )
        
        return {
            "workflow_id": workflow_id,
            "workflow_status": "completed",
            "completion_type": completion_type,
            "total_execution_time_ms": total_time,
            "steps_executed": len(self.execution_history),
            "final_context": self.workflow_context,
            "execution_history": self.execution_history
        }

def test_successful_loan_workflow():
    """Test successful loan approval workflow"""
    print("Testing Successful Loan Workflow with Step Dependencies")
    print("=" * 60)
    
    engine = StepWorkflowEngine()
    engine.load_step_workflow_rules('examples/step_workflow_simple.yml')
    
    # Test data for successful application
    loan_application = {
        "credit_score": 720,
        "annual_income": 75000,
        "debt_to_income_ratio": 0.35,
        "loan_amount": 250000,
        "late_payments_count": 0,
        "income_documents_provided": True,
        "verified_income_ratio": 0.95,
        "loan_to_income_ratio": 3.3
    }
    
    results = engine.execute_step_workflow("LOAN_001", loan_application)
    
    print(f"Workflow Status: {results['workflow_status']}")
    print(f"Completion Type: {results.get('completion_type', 'N/A')}")
    print(f"Total Time: {results.get('total_execution_time_ms', 0):.1f}ms")
    print(f"Steps Executed: {results.get('steps_executed', 0)}")
    
    print("\nStep Execution History:")
    for i, step in enumerate(results['execution_history'], 1):
        status = step['status']
        step_name = step['step']
        time_ms = step.get('execution_time_ms', 0)
        decision = step.get('decision', {}).get('decision', 'N/A') if step.get('decision') else 'N/A'
        print(f"  {i}. {step_name}: {status} ({time_ms:.1f}ms) -> {decision}")
    
    if 'final_context' in results:
        print(f"\nFinal Decision: {results['final_context'].get('previous_step_result', 'Unknown')}")
    
    return results

def test_rejected_loan_workflow():
    """Test rejected loan application workflow"""
    print("\n\nTesting Rejected Loan Workflow")
    print("=" * 60)
    
    engine = StepWorkflowEngine()
    engine.load_step_workflow_rules('examples/step_workflow_simple.yml')
    
    # Test data for rejected application
    loan_application = {
        "credit_score": 480,  # Below minimum
        "annual_income": 30000,
        "debt_to_income_ratio": 0.75,  # Too high
        "loan_amount": 200000,
        "late_payments_count": 6,
        "income_documents_provided": False,
        "verified_income_ratio": 0.6
    }
    
    results = engine.execute_step_workflow("LOAN_002", loan_application)
    
    print(f"Workflow Status: {results['workflow_status']}")
    print(f"Termination Reason: {results.get('termination_reason', 'N/A')}")
    print(f"Steps Executed: {results.get('steps_executed', 0)}")
    
    print("\nStep Execution History:")
    for i, step in enumerate(results['execution_history'], 1):
        status = step['status']
        step_name = step['step']
        print(f"  {i}. {step_name}: {status}")
    
    if 'final_outcome' in results:
        print(f"\nFinal Outcome: {results['final_outcome'].get('decision', 'Unknown')}")
    
    return results

def test_manual_review_workflow():
    """Test manual review workflow path"""
    print("\n\nTesting Manual Review Workflow Path")
    print("=" * 60)
    
    engine = StepWorkflowEngine()
    engine.load_step_workflow_rules('examples/step_workflow_simple.yml')
    
    # Test data for manual review (medium credit score)
    loan_application = {
        "credit_score": 620,  # Medium range
        "annual_income": 55000,
        "debt_to_income_ratio": 0.45,
        "loan_amount": 180000,
        "late_payments_count": 2,
        "income_documents_provided": True,
        "verified_income_ratio": 0.85
    }
    
    results = engine.execute_step_workflow("LOAN_003", loan_application)
    
    print(f"Workflow Status: {results['workflow_status']}")
    print(f"Completion Type: {results.get('completion_type', 'N/A')}")
    print(f"Steps Executed: {results.get('steps_executed', 0)}")
    
    print("\nStep Execution History:")
    for i, step in enumerate(results['execution_history'], 1):
        status = step['status']
        step_name = step['step']
        decision = step.get('decision', {}).get('decision', 'N/A') if step.get('decision') else 'N/A'
        print(f"  {i}. {step_name}: {status} -> {decision}")
    
    return results

def demonstrate_before_after_rules():
    """Demonstrate before/after rule relationships"""
    print("\n\nBefore/After Rule Dependencies Explained")
    print("=" * 60)
    
    print("Step Workflow Structure:")
    print("1. Application Validation")
    print("   └─ BEFORE: No dependencies")
    print("   └─ AFTER: Sets 'previous_step_result' = 'validation_passed'")
    print("")
    print("2. Credit Assessment")  
    print("   └─ BEFORE: Requires previous_step_result = 'validation_passed'")
    print("   └─ AFTER: Sets risk_level and interest_rate")
    print("")
    print("3. Income Verification")
    print("   └─ BEFORE: Requires previous_step_result = 'low_risk_approved'")
    print("   └─ AFTER: Sets verification_status = 'complete'")
    print("")
    print("4. Final Approval")
    print("   └─ BEFORE: Requires previous_step_result = 'income_verified'")
    print("   └─ AFTER: Triggers 'setup_loan_account' if approved")
    print("")
    print("5. Account Setup (After Rule)")
    print("   └─ BEFORE: Triggered by final approval")
    print("   └─ AFTER: Creates account and payment schedule")
    print("")
    print("Alternative Paths:")
    print("• Manual Review: When credit score 580-649")
    print("• Rejection: When validation fails or risk too high")

def main():
    """Run complete step-based workflow demonstration"""
    print("LogicBridge Step-Based Workflow with Before/After Dependencies")
    print("=" * 70)
    
    # Test successful workflow
    success_results = test_successful_loan_workflow()
    
    # Test rejected workflow  
    rejection_results = test_rejected_loan_workflow()
    
    # Test manual review path
    manual_results = test_manual_review_workflow()
    
    # Explain the dependency system
    demonstrate_before_after_rules()
    
    print("\n" + "=" * 70)
    print("Step-Based Workflow Features Implemented:")
    print("✓ Sequential step execution with dependencies")
    print("✓ Before rule conditions (steps must pass previous checks)")
    print("✓ After rule actions (trigger subsequent processes)")
    print("✓ Context propagation between steps")
    print("✓ Alternative workflow paths")
    print("✓ Early termination with proper cleanup")
    print("✓ Complete audit trail for each step")
    print("✓ Performance timing for each step")

if __name__ == "__main__":
    main()