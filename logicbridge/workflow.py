"""
Workflow and step-based rule execution module
Implements rule dependencies, before/after relationships, and sequential processing
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import time
import json
from .core import RuleEngine, Decision
from .audit import AuditLogger

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class RuleStep:
    """Represents a single step in a workflow with dependencies"""
    id: str
    rule_id: str
    description: str
    depends_on: Optional[List[str]] = None  # List of step IDs this step depends on
    preconditions: Optional[List[str]] = None  # List of rule IDs that must succeed first
    postconditions: Optional[List[str]] = None  # List of rule IDs to execute after this
    condition: Optional[Dict[str, Any]] = None  # Additional condition to run this step
    timeout_seconds: int = 300
    retry_count: int = 0
    parallel_group: Optional[str] = None  # Steps in same group can run in parallel

@dataclass
class WorkflowExecution:
    """Tracks execution state of a workflow"""
    workflow_id: str
    steps: Dict[str, RuleStep]
    step_status: Dict[str, StepStatus]
    step_results: Dict[str, Optional[Decision]]
    step_start_times: Dict[str, float]
    step_end_times: Dict[str, float]
    execution_context: Dict[str, Any]
    total_start_time: float
    
class WorkflowEngine:
    """Manages step-based rule execution with dependencies"""
    
    def __init__(self, rule_engine: RuleEngine, audit_logger: AuditLogger):
        self.rule_engine = rule_engine
        self.audit_logger = audit_logger
        self.active_workflows: Dict[str, WorkflowExecution] = {}
    
    def create_workflow(self, workflow_id: str, steps: List[RuleStep]) -> WorkflowExecution:
        """Create a new workflow with step dependencies"""
        # Validate dependencies
        step_ids = {step.id for step in steps}
        for step in steps:
            if step.depends_on:
                missing_deps = set(step.depends_on) - step_ids
                if missing_deps:
                    raise ValueError(f"Step {step.id} has missing dependencies: {missing_deps}")
        
        # Initialize workflow execution
        workflow = WorkflowExecution(
            workflow_id=workflow_id,
            steps={step.id: step for step in steps},
            step_status={step.id: StepStatus.PENDING for step in steps},
            step_results={step.id: None for step in steps},
            step_start_times={},
            step_end_times={},
            execution_context={},
            total_start_time=time.time()
        )
        
        self.active_workflows[workflow_id] = workflow
        
        # Log workflow creation
        self.audit_logger.log_ruleset_change(
            rule_sha=f"workflow_{workflow_id}",
            author="workflow_engine",
            content=f"Created workflow with {len(steps)} steps: {[s.id for s in steps]}"
        )
        
        return workflow
    
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow with step dependencies and before/after rules"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.active_workflows[workflow_id]
        workflow.execution_context.update(input_data)
        
        # Execute steps in dependency order
        while self._has_pending_steps(workflow):
            ready_steps = self._get_ready_steps(workflow)
            
            if not ready_steps:
                # Check for circular dependencies or blocked workflow
                pending_steps = [sid for sid, status in workflow.step_status.items() 
                               if status == StepStatus.PENDING]
                raise RuntimeError(f"Workflow {workflow_id} is blocked. Pending steps: {pending_steps}")
            
            # Execute ready steps (potentially in parallel)
            parallel_groups = self._group_parallel_steps(ready_steps, workflow)
            
            for group_steps in parallel_groups:
                if len(group_steps) == 1:
                    # Single step execution
                    self._execute_step(group_steps[0], workflow)
                else:
                    # Parallel execution (for future enhancement)
                    for step_id in group_steps:
                        self._execute_step(step_id, workflow)
        
        # Generate final results
        return self._generate_workflow_results(workflow)
    
    def _has_pending_steps(self, workflow: WorkflowExecution) -> bool:
        """Check if workflow has any pending steps"""
        return any(status == StepStatus.PENDING for status in workflow.step_status.values())
    
    def _get_ready_steps(self, workflow: WorkflowExecution) -> List[str]:
        """Get steps that are ready to execute (all dependencies completed)"""
        ready_steps = []
        
        for step_id, step in workflow.steps.items():
            if workflow.step_status[step_id] != StepStatus.PENDING:
                continue
            
            # Check dependencies
            if step.depends_on:
                deps_completed = all(
                    workflow.step_status.get(dep_id) == StepStatus.COMPLETED
                    for dep_id in step.depends_on
                )
                if not deps_completed:
                    continue
            
            # Check preconditions (before rules)
            if step.preconditions:
                preconditions_met = self._check_preconditions(step, workflow)
                if not preconditions_met:
                    continue
            
            # Check step-specific condition
            if step.condition:
                condition_met = self._evaluate_step_condition(step, workflow)
                if not condition_met:
                    workflow.step_status[step_id] = StepStatus.SKIPPED
                    continue
            
            ready_steps.append(step_id)
        
        return ready_steps
    
    def _check_preconditions(self, step: RuleStep, workflow: WorkflowExecution) -> bool:
        """Check if precondition rules have been satisfied"""
        for precondition_rule_id in step.preconditions:
            # Look for successful execution of precondition rule in previous steps
            precondition_met = False
            for step_result in workflow.step_results.values():
                if (step_result and 
                    step_result.rule_id == precondition_rule_id and
                    step_result.outcome.get("decision") in ["approve", "pass", "success"]):
                    precondition_met = True
                    break
            
            if not precondition_met:
                return False
        
        return True
    
    def _evaluate_step_condition(self, step: RuleStep, workflow: WorkflowExecution) -> bool:
        """Evaluate step-specific condition"""
        if not step.condition:
            return True
        
        # Simple condition evaluation (can be enhanced)
        condition_type = step.condition.get("type")
        field = step.condition.get("field")
        value = step.condition.get("value")
        
        context_value = workflow.execution_context.get(field)
        
        if condition_type == "equals":
            return context_value == value
        elif condition_type == "greater_than":
            return context_value > value
        elif condition_type == "contains":
            return value in context_value if context_value else False
        
        return True
    
    def _group_parallel_steps(self, ready_steps: List[str], workflow: WorkflowExecution) -> List[List[str]]:
        """Group steps that can be executed in parallel"""
        parallel_groups = {}
        sequential_steps = []
        
        for step_id in ready_steps:
            step = workflow.steps[step_id]
            if step.parallel_group:
                if step.parallel_group not in parallel_groups:
                    parallel_groups[step.parallel_group] = []
                parallel_groups[step.parallel_group].append(step_id)
            else:
                sequential_steps.append([step_id])
        
        # Combine parallel groups and sequential steps
        result = list(parallel_groups.values()) + sequential_steps
        return result
    
    def _execute_step(self, step_id: str, workflow: WorkflowExecution):
        """Execute a single workflow step"""
        step = workflow.steps[step_id]
        workflow.step_status[step_id] = StepStatus.RUNNING
        workflow.step_start_times[step_id] = time.time()
        
        try:
            # Prepare evaluation data with accumulated context
            evaluation_data = {**workflow.execution_context}
            
            # Add results from previous steps
            for prev_step_id, prev_result in workflow.step_results.items():
                if prev_result:
                    evaluation_data[f"step_{prev_step_id}_result"] = prev_result.outcome
            
            # Execute the rule
            decision = self.rule_engine.evaluate(evaluation_data)
            
            if decision and decision.rule_id == step.rule_id:
                workflow.step_status[step_id] = StepStatus.COMPLETED
                workflow.step_results[step_id] = decision
                
                # Update execution context with step results
                workflow.execution_context.update(decision.outcome)
                
                # Execute postconditions (after rules)
                if step.postconditions:
                    self._execute_postconditions(step, workflow, evaluation_data)
                
                # Log successful step execution
                self.audit_logger.log_decision(decision)
                
            else:
                workflow.step_status[step_id] = StepStatus.FAILED
                self.audit_logger.log_ruleset_change(
                    rule_sha=f"workflow_{workflow.workflow_id}_step_{step_id}",
                    author="workflow_engine",
                    content=f"Step {step_id} failed: no matching rule {step.rule_id}"
                )
        
        except Exception as e:
            workflow.step_status[step_id] = StepStatus.FAILED
            self.audit_logger.log_ruleset_change(
                rule_sha=f"workflow_{workflow.workflow_id}_step_{step_id}",
                author="workflow_engine",
                content=f"Step {step_id} failed with error: {str(e)}"
            )
        
        finally:
            workflow.step_end_times[step_id] = time.time()
    
    def _execute_postconditions(self, step: RuleStep, workflow: WorkflowExecution, 
                               evaluation_data: Dict[str, Any]):
        """Execute postcondition rules after step completion"""
        for postcondition_rule_id in step.postconditions:
            try:
                # Create temporary context for postcondition
                postcondition_data = {
                    **evaluation_data,
                    f"after_{step.id}": True,
                    "trigger_rule": postcondition_rule_id
                }
                
                postcondition_decision = self.rule_engine.evaluate(postcondition_data)
                if postcondition_decision:
                    # Log postcondition execution
                    self.audit_logger.log_decision(postcondition_decision)
                    
                    # Update context with postcondition results
                    workflow.execution_context.update({
                        f"postcondition_{postcondition_rule_id}": postcondition_decision.outcome
                    })
            
            except Exception as e:
                self.audit_logger.log_ruleset_change(
                    rule_sha=f"postcondition_{postcondition_rule_id}",
                    author="workflow_engine",
                    content=f"Postcondition {postcondition_rule_id} failed: {str(e)}"
                )
    
    def _generate_workflow_results(self, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Generate final workflow execution results"""
        total_time = time.time() - workflow.total_start_time
        
        step_summaries = {}
        for step_id, step in workflow.steps.items():
            step_time = 0
            if (step_id in workflow.step_start_times and 
                step_id in workflow.step_end_times):
                step_time = workflow.step_end_times[step_id] - workflow.step_start_times[step_id]
            
            step_summaries[step_id] = {
                "status": workflow.step_status[step_id].value,
                "execution_time_ms": step_time * 1000,
                "result": workflow.step_results[step_id].outcome if workflow.step_results[step_id] else None
            }
        
        # Calculate workflow statistics
        completed_steps = sum(1 for status in workflow.step_status.values() 
                            if status == StepStatus.COMPLETED)
        failed_steps = sum(1 for status in workflow.step_status.values() 
                         if status == StepStatus.FAILED)
        
        results = {
            "workflow_id": workflow.workflow_id,
            "total_execution_time_ms": total_time * 1000,
            "total_steps": len(workflow.steps),
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "success_rate": completed_steps / len(workflow.steps) if workflow.steps else 0,
            "final_context": workflow.execution_context,
            "step_details": step_summaries
        }
        
        # Log workflow completion
        self.audit_logger.log_ruleset_change(
            rule_sha=f"workflow_{workflow.workflow_id}_complete",
            author="workflow_engine",
            content=json.dumps(results)
        )
        
        return results

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow"""
        if workflow_id not in self.active_workflows:
            return None
        
        workflow = self.active_workflows[workflow_id]
        return {
            "workflow_id": workflow_id,
            "step_status": {k: v.value for k, v in workflow.step_status.items()},
            "execution_context": workflow.execution_context,
            "start_time": workflow.total_start_time
        }