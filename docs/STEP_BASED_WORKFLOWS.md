# Step-Based Workflows with Before/After Rule Dependencies

## Overview

Newton.RS supports step-based workflows where rules can reference other rules through before/after dependencies. This enables complex business processes with sequential execution, conditional logic, and context propagation.


## Architecture

### Core Components

1. **Step Workflow Engine** (`step_workflow_implementation.py`)
   - Manages sequential rule execution
   - Handles before/after dependencies
   - Maintains execution context between steps
   - Provides complete audit trail

2. **Rule Dependency System**
   - Before rules: Conditions that must be met to execute a step
   - After rules: Actions triggered when a step completes
   - Context propagation: Results flow between steps

3. **Database Integration**
   - Every step execution is logged to the audit database
   - Complete traceability of workflow execution
   - Performance metrics for each step

## Rule Encoding for Step-Based Workflows

### Basic Step Structure

```yaml
- id: "step_rule_name"
  description: "Step description"
  tags: ["step_2", "credit_assessment"]
  when:
    type: "and"
    conditions:
      # Before rule dependency
      - type: "equals"
        field: "previous_step_result"
        value: "validation_passed"
      # Business logic conditions
      - type: "greater_than"
        field: "credit_score"
        value: 650
  then:
    outcome:
      decision: "low_risk_approved"
      step: "credit_assessment"
      next_step: "income_verification"
      # After rule trigger
      trigger_after_rule: "setup_notifications"
```

### Before Rule Dependencies

Rules can require specific previous step outcomes:

```yaml
# Step 2 depends on Step 1 success
when:
  type: "and"
  conditions:
    - type: "equals"
      field: "previous_step_result"
      value: "validation_passed"
    - type: "greater_than"
      field: "credit_score"
      value: 650
```

### After Rule Actions

Rules can trigger subsequent actions:

```yaml
then:
  outcome:
    decision: "loan_approved"
    # Trigger account setup after approval
    trigger_after_rule: "setup_loan_account"
```

## Complete Workflow Example

### Loan Approval Process

```yaml
version: "1.0"
rules:
  # Step 1: Validation (no dependencies)
  - id: "validate_loan_application"
    when:
      type: "and"
      conditions:
        - type: "greater_than"
          field: "credit_score"
          value: 500
        - type: "less_than"
          field: "debt_to_income_ratio"
          value: 0.7
    then:
      outcome:
        decision: "validation_passed"
        next_step: "credit_assessment"

  # Step 2: Credit Assessment (AFTER validation)
  - id: "assess_credit_risk_step"
    when:
      type: "and"
      conditions:
        # BEFORE rule: validation must pass
        - type: "equals"
          field: "previous_step_result"
          value: "validation_passed"
        - type: "greater_than"
          field: "credit_score"
          value: 650
    then:
      outcome:
        decision: "low_risk_approved"
        risk_level: "low"
        next_step: "income_verification"

  # Step 3: Income Verification (AFTER credit assessment)
  - id: "verify_income_step"
    when:
      type: "and"
      conditions:
        # BEFORE rule: credit assessment must succeed
        - type: "equals"
          field: "previous_step_result"
          value: "low_risk_approved"
        - type: "equals"
          field: "income_documents_provided"
          value: true
    then:
      outcome:
        decision: "income_verified"
        next_step: "final_approval"

  # Step 4: Final Approval (AFTER income verification)
  - id: "final_loan_approval_step"
    when:
      type: "and"
      conditions:
        # BEFORE rule: income must be verified
        - type: "equals"
          field: "previous_step_result"
          value: "income_verified"
        - type: "less_than"
          field: "loan_amount"
          value: 500000
    then:
      outcome:
        decision: "loan_approved"
        # AFTER rule: trigger account setup
        trigger_after_rule: "setup_loan_account"

  # After Rule: Account Setup
  - id: "setup_loan_account"
    when:
      type: "equals"
      field: "trigger_after_rule"
      value: "setup_loan_account"
    then:
      outcome:
        decision: "account_created"
        account_number: "LN{{ timestamp }}"
```

## Implementation Features

### Sequential Execution

Steps execute in dependency order:

```python
# Step execution with before/after handling
def _execute_step(self, step_name: str, rule_target: str, data: Dict[str, Any], 
                 before_condition: Optional[callable] = None) -> Optional[Dict[str, Any]]:
    
    # Check before condition
    if before_condition and not before_condition():
        return None
    
    # Execute rule
    decision = self.rule_engine.evaluate(data)
    
    # Handle after actions
    if decision and "trigger_after_rule" in decision.outcome:
        self._execute_after_rule(decision.outcome["trigger_after_rule"])
    
    return decision.outcome
```

### Context Propagation

Results flow between steps:

```python
# Update context after each step
self.workflow_context.update({
    "previous_step_result": step_result["decision"],
    "risk_level": step_result.get("risk_level"),
    "interest_rate": step_result.get("interest_rate")
})
```

### Alternative Paths

Workflows can branch based on conditions:

```python
# Check alternative path if main path fails
if not step2_result:
    manual_review_result = self._execute_step(
        step_name="manual_review_check",
        rule_target="manual_review_required", 
        data=self.workflow_context
    )
    if manual_review_result:
        return self._finalize_workflow(workflow_id, start_time, "manual_review_path")
```

## Execution Results

### Successful Workflow Output

```json
{
  "workflow_id": "LOAN_001",
  "workflow_status": "completed",
  "completion_type": "successful_completion",
  "total_execution_time_ms": 45.2,
  "steps_executed": 5,
  "execution_history": [
    {
      "step": "application_validation",
      "status": "completed",
      "decision": {"decision": "validation_passed"},
      "execution_time_ms": 8.1
    },
    {
      "step": "credit_assessment",
      "status": "completed", 
      "decision": {"decision": "low_risk_approved", "risk_level": "low"},
      "execution_time_ms": 12.3
    },
    {
      "step": "income_verification",
      "status": "completed",
      "decision": {"decision": "income_verified"},
      "execution_time_ms": 9.7
    },
    {
      "step": "final_approval",
      "status": "completed",
      "decision": {"decision": "loan_approved"},
      "execution_time_ms": 11.4
    },
    {
      "step": "account_setup",
      "status": "completed",
      "decision": {"decision": "account_created"},
      "execution_time_ms": 3.7
    }
  ]
}
```

## Database Audit Trail

Every step execution creates audit entries:

```sql
-- Rule changes table tracks workflow execution
INSERT INTO rule_changes (
    rule_sha,
    author,
    timestamp,
    content
) VALUES (
    'workflow_LOAN_001',
    'step_workflow_engine',
    '2025-06-09T21:18:49Z',
    'Workflow completed: successful_completion'
);

-- Decisions table tracks each step
INSERT INTO decisions (
    rule_id,
    rule_sha,
    outcome,
    elapsed_us,
    timestamp
) VALUES (
    'validate_loan_application',
    'step_workflow_hash',
    '{"decision": "validation_passed", "step": "application_validation"}',
    8100,
    '2025-06-09T21:18:49Z'
);
```

## Advanced Patterns

### Parallel Execution Groups

Steps can execute in parallel when dependencies allow:

```yaml
- id: "fraud_screening"
  tags: ["parallel_group_1"]
  # Executes in parallel with other group_1 steps

- id: "compliance_check" 
  tags: ["parallel_group_1"]
  # Executes in parallel with fraud_screening
```

### Conditional Step Execution

Steps can be skipped based on runtime conditions:

```yaml
- id: "manual_underwriting"
  when:
    type: "and"
    conditions:
      - type: "equals"
        field: "requires_manual_review"
        value: true
      - type: "range"
        field: "credit_score"
        min: 580
        max: 649
```

### Error Handling and Recovery

Workflows handle failures gracefully:

```python
def _handle_early_termination(self, reason: str, last_result: Optional[Dict[str, Any]]):
    # Check for rejection handling rules
    rejection_decision = self.rule_engine.evaluate({
        **self.workflow_context,
        "termination_reason": reason
    })
    
    return {
        "workflow_status": "terminated",
        "termination_reason": reason,
        "final_outcome": rejection_decision.outcome if rejection_decision else None
    }
```

## Integration with LogicBridge API

Step-based workflows integrate seamlessly with existing LogicBridge features:

1. **Rule Generation**: LLM can generate step-based rules from user stories
2. **Validation**: Step workflows validate against the same JSON schema
3. **Audit System**: Complete traceability through existing audit database
4. **Performance**: Optimized for high-throughput step processing

## Use Cases

### Financial Services
- Loan approval workflows with multiple validation steps
- KYC/AML compliance processes with sequential checks
- Risk assessment pipelines with escalation paths

### E-commerce
- Order processing with inventory, payment, and fulfillment steps
- Customer onboarding with progressive validation
- Return/refund workflows with approval chains

### Insurance
- Claims processing with multiple review stages
- Underwriting workflows with risk assessment steps
- Policy renewal processes with eligibility checks

## Performance Characteristics

- **Step Execution**: 8-15ms per step typical
- **Context Propagation**: Constant time complexity
- **Database Logging**: Asynchronous, minimal overhead
- **Memory Usage**: Linear with workflow size
- **Scalability**: Supports hundreds of steps per workflow

This implementation provides a robust foundation for complex business process automation while maintaining LogicBridge's core principles of determinism, auditability, and performance.