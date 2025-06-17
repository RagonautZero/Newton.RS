# Newton.RS Rule Chaining and Process Workflows


## Architecture Overview

Newton.RS consists of two core modules backed by a database:

### Module 1: Rule Generation (`llm_generator.py`)
- **Purpose**: Convert natural language business requirements into executable rules
- **Input**: User stories, business requirements in plain English
- **Output**: Structured YAML/JSON rule definitions
- **Providers**: OpenAI GPT-4o, Ollama local models, Mock for testing

### Module 2: Audit System (`audit.py`)
- **Purpose**: Track all rule changes, decisions, and system activity
- **Database**: SQLite (development) or PostgreSQL (production)
- **Storage**: Rule versions, decision history, performance metrics
- **Features**: SHA-based versioning, complete audit trail

## Rule Encoding Structure

Rules are encoded in a declarative DSL format:

```yaml
version: "1.0"
rules:
  - id: "unique_rule_identifier"
    description: "Human-readable description"
    tags: ["domain", "priority", "category"]
    priority: 100  # Optional: Higher numbers = higher priority
    when:
      # Condition logic
    then:
      outcome:
        # Decision output
```

## Rule Chaining Patterns

### Pattern 1: Application-Level Orchestration

The most flexible approach - implement chaining in your application code:

```python
from logicbridge.core import RuleEngine
import yaml

class BusinessProcessOrchestrator:
    def __init__(self):
        self.engine = RuleEngine()
        
    def load_process_rules(self, process_name: str):
        """Load rules for a specific business process"""
        # Load different rulesets for different processes
        ruleset_map = {
            "loan_approval": "rulesets/loan_approval.yml",
            "fraud_detection": "rulesets/fraud_detection.yml",
            "customer_onboarding": "rulesets/customer_onboarding.yml"
        }
        
        if process_name in ruleset_map:
            self.engine.load_ruleset_from_file(ruleset_map[process_name])
    
    def execute_loan_approval_process(self, application_data):
        """Multi-step loan approval process"""
        results = []
        
        # Step 1: Credit check
        self.load_process_rules("credit_check")
        credit_decision = self.engine.evaluate(application_data)
        results.append(("credit_check", credit_decision))
        
        if credit_decision and credit_decision.outcome.get("decision") == "pass":
            # Step 2: Income verification
            self.load_process_rules("income_verification")
            income_decision = self.engine.evaluate(application_data)
            results.append(("income_verification", income_decision))
            
            if income_decision and income_decision.outcome.get("decision") == "verified":
                # Step 3: Final approval
                self.load_process_rules("final_approval")
                final_decision = self.engine.evaluate({
                    **application_data,
                    "credit_passed": True,
                    "income_verified": True
                })
                results.append(("final_approval", final_decision))
        
        return results

# Usage
orchestrator = BusinessProcessOrchestrator()
application = {
    "credit_score": 750,
    "annual_income": 80000,
    "loan_amount": 200000,
    "debt_to_income": 0.3
}

process_results = orchestrator.execute_loan_approval_process(application)
```

### Pattern 2: Priority-Based Rule Ordering

Implement rule priorities within a single ruleset:

```yaml
version: "1.0"
rules:
  # High priority - security checks first
  - id: "fraud_detection"
    priority: 1000
    description: "Detect fraudulent activity"
    when:
      type: "or"
      conditions:
        - type: "greater_than"
          field: "velocity_score"
          value: 0.8
        - type: "equals"
          field: "blacklisted"
          value: true
    then:
      outcome:
        decision: "block_transaction"
        reason: "Fraud risk detected"
        stop_processing: true

  # Medium priority - business rules
  - id: "premium_customer_benefits"
    priority: 500
    description: "Apply premium customer benefits"
    when:
      type: "and"
      conditions:
        - type: "equals"
          field: "customer_tier"
          value: "premium"
        - type: "not_equals"
          field: "previous_decision"
          value: "block_transaction"
    then:
      outcome:
        decision: "apply_benefits"
        discount_percent: 15
        priority_support: true

  # Low priority - default handling
  - id: "standard_processing"
    priority: 100
    description: "Standard transaction processing"
    when:
      type: "equals"
      field: "status"
      value: "active"
    then:
      outcome:
        decision: "approve"
        processing_tier: "standard"
```

### Pattern 3: External Workflow Engine Integration

Integrate with workflow engines like Temporal, Airflow, or AWS Step Functions:

```python
# Example with Temporal workflow
from temporalio import workflow, activity
from logicbridge.core import RuleEngine
from datetime import timedelta

class LoanApprovalWorkflow:
    @workflow.defn
    class LoanApprovalWorkflow:
        @workflow.run
        async def run(self, application_data: dict) -> dict:
            # Step 1: Initial screening
            screening_result = await workflow.execute_activity(
                evaluate_rules,
                args=["initial_screening", application_data],
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            if screening_result.get("decision") != "pass":
                return {"status": "rejected", "reason": "Failed initial screening"}
            
            # Step 2: Credit assessment
            credit_result = await workflow.execute_activity(
                evaluate_rules,
                args=["credit_assessment", {**application_data, **screening_result}],
                start_to_close_timeout=timedelta(seconds=60)
            )
            
            # Step 3: Manual review if needed
            if credit_result.get("requires_manual_review"):
                manual_result = await workflow.execute_activity(
                    request_manual_review,
                    args=[application_data, credit_result],
                    start_to_close_timeout=timedelta(hours=24)
                )
                return manual_result
            
            # Step 4: Final decision
            final_result = await workflow.execute_activity(
                evaluate_rules,
                args=["final_decision", {**application_data, **credit_result}],
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            return final_result

@activity.defn
async def evaluate_rules(ruleset_name: str, data: dict) -> dict:
    engine = RuleEngine()
    engine.load_ruleset_from_file(f"rulesets/{ruleset_name}.yml")
    decision = engine.evaluate(data)
    return decision.outcome if decision else {"decision": "no_match"}
```

## Database-Backed Rule Management

The audit system provides complete traceability:

```python
from logicbridge.audit import AuditLogger

# Initialize audit logger
audit = AuditLogger("logicbridge_audit.db")

# Track rule changes
audit.log_ruleset_change(
    rule_sha="abc123def456",
    author="business_analyst",
    content="Updated premium customer discount rules",
    llm_model="gpt-4o"  # If generated by LLM
)

# Track decisions across process steps
def track_process_decisions(process_id: str, decisions: list):
    for step, decision in decisions:
        if decision:
            # Enhance decision with process context
            enhanced_decision = Decision(
                rule_id=f"{process_id}_{step}_{decision.rule_id}",
                outcome={**decision.outcome, "process_step": step},
                matched_conditions=decision.matched_conditions,
                elapsed_us=decision.elapsed_us,
                timestamp=decision.timestamp,
                rule_sha=decision.rule_sha
            )
            audit.log_decision(enhanced_decision)

# Query decision history for analysis
process_decisions = audit.get_log_entries(limit=100, since="7d")
```

## Advanced Process Patterns

### Sequential Processing with State

```python
class StatefulProcessor:
    def __init__(self):
        self.engine = RuleEngine()
        self.state = {}
    
    def process_with_state(self, data: dict, ruleset_sequence: list) -> dict:
        """Process through multiple rulesets maintaining state"""
        for ruleset_name in ruleset_sequence:
            self.engine.load_ruleset_from_file(f"rulesets/{ruleset_name}.yml")
            
            # Merge current state with input data
            evaluation_data = {**data, **self.state}
            decision = self.engine.evaluate(evaluation_data)
            
            if decision:
                # Update state with decision outcomes
                self.state.update(decision.outcome)
                
                # Check for stop conditions
                if decision.outcome.get("stop_processing"):
                    break
        
        return self.state

# Usage
processor = StatefulProcessor()
result = processor.process_with_state(
    {"customer_id": "12345", "transaction_amount": 5000},
    ["fraud_check", "risk_assessment", "approval_logic"]
)
```

### Parallel Rule Evaluation

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelRuleProcessor:
    def __init__(self):
        self.engines = {}
    
    async def evaluate_parallel(self, data: dict, rulesets: list) -> dict:
        """Evaluate multiple rulesets in parallel"""
        
        def evaluate_ruleset(ruleset_name):
            if ruleset_name not in self.engines:
                self.engines[ruleset_name] = RuleEngine()
                self.engines[ruleset_name].load_ruleset_from_file(
                    f"rulesets/{ruleset_name}.yml"
                )
            
            return (ruleset_name, self.engines[ruleset_name].evaluate(data))
        
        # Execute in parallel
        with ThreadPoolExecutor(max_workers=len(rulesets)) as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, evaluate_ruleset, ruleset)
                for ruleset in rulesets
            ]
            results = await asyncio.gather(*tasks)
        
        # Combine results
        combined_results = {}
        for ruleset_name, decision in results:
            if decision:
                combined_results[ruleset_name] = decision.outcome
        
        return combined_results

# Usage
processor = ParallelRuleProcessor()
results = await processor.evaluate_parallel(
    {"customer_tier": "premium", "order_total": 500},
    ["discount_rules", "shipping_rules", "loyalty_rules"]
)
```

## Best Practices for Rule Chaining

### 1. Design for Auditability
```python
# Always log process context
def log_process_step(step_name: str, input_data: dict, decision: Decision):
    audit_logger.log_decision(Decision(
        rule_id=f"process_step_{step_name}_{decision.rule_id}",
        outcome={
            **decision.outcome,
            "process_step": step_name,
            "input_hash": hash(str(sorted(input_data.items())))
        },
        matched_conditions=decision.matched_conditions,
        elapsed_us=decision.elapsed_us,
        timestamp=decision.timestamp,
        rule_sha=decision.rule_sha
    ))
```

### 2. Handle Failures Gracefully
```python
def safe_rule_evaluation(engine: RuleEngine, data: dict) -> Optional[Decision]:
    try:
        return engine.evaluate(data)
    except Exception as e:
        audit_logger.log_ruleset_change(
            rule_sha="error",
            author="system",
            content=f"Rule evaluation error: {str(e)}"
        )
        return None
```

### 3. Implement Circuit Breakers
```python
class RuleCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.last_failure_time = 0
        self.timeout = timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call_with_circuit_breaker(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise e
```

## Production Deployment Considerations

### Database Configuration
```python
# For production, use PostgreSQL
DATABASE_URL = "postgresql://user:password@host:port/logicbridge_db"

# Configure connection pooling
audit_logger = AuditLogger(
    db_url=DATABASE_URL,
    pool_size=20,
    max_overflow=30
)
```

### Performance Optimization
```python
# Cache compiled rules for repeated use
from functools import lru_cache

class OptimizedRuleEngine:
    def __init__(self):
        self.engine = RuleEngine()
        self.cached_rulesets = {}
    
    @lru_cache(maxsize=100)
    def get_cached_ruleset(self, ruleset_hash: str):
        return self.cached_rulesets.get(ruleset_hash)
    
    def evaluate_with_cache(self, ruleset_name: str, data: dict):
        # Use cached compiled rules for better performance
        if ruleset_name not in self.cached_rulesets:
            self.engine.load_ruleset_from_file(f"rulesets/{ruleset_name}.yml")
            self.cached_rulesets[ruleset_name] = self.engine.get_ruleset_sha()
        
        return self.engine.evaluate(data)
```

This architecture provides maximum flexibility for implementing complex business processes while maintaining complete auditability and traceability through the database-backed audit system.