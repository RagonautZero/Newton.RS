"""
FastAPI REST API for LogicBridge rule engine
"""

import os
import json
import tempfile
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .core import RuleEngine, Decision, RuleValidationError, ExecutionError
from .audit import AuditLogger
from .validation import validate_ruleset_schema


class EvaluationRequest(BaseModel):
    payload: Dict[str, Any] = Field(..., description="Data payload to evaluate")
    
    
class BatchEvaluationRequest(BaseModel):
    events: List[Dict[str, Any]] = Field(..., description="List of events to evaluate")


class RulesetUploadRequest(BaseModel):
    content: str = Field(..., description="Ruleset content (YAML or JSON)")
    format: str = Field("yaml", description="Format: 'yaml' or 'json'")


class DecisionResponse(BaseModel):
    rule_id: str
    outcome: Dict[str, Any]
    matched_conditions: List[str]
    elapsed_us: int
    timestamp: int
    rule_sha: str


class BatchDecisionResponse(BaseModel):
    decisions: List[Optional[DecisionResponse]]


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="LogicBridge Rule Engine API",
        description="Deterministic rule engine with LLM integration",
        version="1.0.0"
    )
    
    # Mount static files and templates
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")
    
    # Global rule engine instance
    rule_engine = RuleEngine()
    audit_logger = AuditLogger()
    
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Serve the main web interface"""
        return templates.TemplateResponse("index.html", {"request": request})
    
    @app.post("/api/ruleset/upload")
    async def upload_ruleset(request: RulesetUploadRequest):
        """Upload and load a new ruleset"""
        try:
            # Validate schema first
            validate_ruleset_schema(request.content, request.format)
            
            # Load into engine
            if request.format == "yaml":
                rule_engine.load_ruleset_from_yaml(request.content)
            else:
                rule_engine.load_ruleset_from_json(request.content)
            
            # Log the change
            rule_sha = rule_engine.get_ruleset_sha()
            audit_logger.log_ruleset_change(
                rule_sha=rule_sha or "unknown",
                author="api_user",
                content=request.content
            )
            
            return {"message": "Ruleset loaded successfully", "rule_sha": rule_sha}
            
        except RuleValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {e}")
    
    @app.post("/api/ruleset/upload-file")
    async def upload_ruleset_file(file: UploadFile = File(...)):
        """Upload ruleset from file"""
        try:
            content = await file.read()
            content_str = content.decode('utf-8')
            
            # Determine format from filename
            format = "yaml" if file.filename.endswith(('.yml', '.yaml')) else "json"
            
            # Validate and load
            validate_ruleset_schema(content_str, format)
            
            if format == "yaml":
                rule_engine.load_ruleset_from_yaml(content_str)
            else:
                rule_engine.load_ruleset_from_json(content_str)
            
            # Log the change
            rule_sha = rule_engine.get_ruleset_sha()
            audit_logger.log_ruleset_change(
                rule_sha=rule_sha or "unknown",
                author="api_user",
                content=content_str
            )
            
            return {"message": "Ruleset loaded successfully", "rule_sha": rule_sha}
            
        except RuleValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {e}")
    
    @app.post("/api/evaluate", response_model=Optional[DecisionResponse])
    async def evaluate_single(request: EvaluationRequest):
        """Evaluate a single payload against loaded rules"""
        try:
            decision = rule_engine.evaluate(request.payload)
            
            if decision:
                # Log the decision
                audit_logger.log_decision(decision)
                
                return DecisionResponse(
                    rule_id=decision.rule_id,
                    outcome=decision.outcome,
                    matched_conditions=decision.matched_conditions,
                    elapsed_us=decision.elapsed_us,
                    timestamp=decision.timestamp,
                    rule_sha=decision.rule_sha
                )
            else:
                return None
                
        except ExecutionError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {e}")
    
    @app.post("/api/evaluate-batch", response_model=BatchDecisionResponse)
    async def evaluate_batch(request: BatchEvaluationRequest):
        """Evaluate multiple events in batch"""
        try:
            decisions = rule_engine.evaluate_many(request.events)
            
            # Log all decisions
            for decision in decisions:
                if decision:
                    audit_logger.log_decision(decision)
            
            decision_responses = []
            for decision in decisions:
                if decision:
                    decision_responses.append(DecisionResponse(
                        rule_id=decision.rule_id,
                        outcome=decision.outcome,
                        matched_conditions=decision.matched_conditions,
                        elapsed_us=decision.elapsed_us,
                        timestamp=decision.timestamp,
                        rule_sha=decision.rule_sha
                    ))
                else:
                    decision_responses.append(None)
            
            return BatchDecisionResponse(decisions=decision_responses)
            
        except ExecutionError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {e}")
    
    @app.get("/api/ruleset/status")
    async def get_ruleset_status():
        """Get current ruleset status"""
        rule_sha = rule_engine.get_ruleset_sha()
        return {
            "loaded": rule_sha is not None,
            "rule_sha": rule_sha,
            "timestamp": audit_logger.get_latest_change_timestamp()
        }
    
    @app.get("/api/audit/log")
    async def get_audit_log(limit: int = 100, since: Optional[str] = None):
        """Get audit log entries"""
        entries = audit_logger.get_log_entries(limit=limit, since=since)
        return {
            "entries": entries,
            "total": len(entries),
            "limit": limit,
            "since": since
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "version": "1.0.0"}
    
    return app


if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=5000)
