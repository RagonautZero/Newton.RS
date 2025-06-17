# Newton.RS API Documentation

## Overview

Newton.RS is a deterministic rule engine with LLM integration designed for auditable business rule validation and generation. It provides REST APIs for rule management, evaluation, and audit logging with comprehensive business scenario support.


## Base URL
```
http://localhost:5000
```

## Authentication
Currently, no authentication is required for API access.

## Content Types
- Request: `application/json`
- Response: `application/json`

---

## API Endpoints

### 1. Root Endpoint
**GET /** 

Returns the web interface for interactive rule testing and management.

**Response:** HTML web interface

---

### 2. Upload Ruleset (JSON Payload)
**POST /api/ruleset/upload**

Upload and activate a new ruleset from JSON payload.

**Request Body:**
```json
{
  "content": "string",     // YAML or JSON ruleset content
  "format": "yaml|json"    // Format specification (default: yaml)
}
```

**Response:**
```json
{
  "message": "Ruleset loaded successfully",
  "sha": "abc123...",
  "rules_count": 5
}
```

**Status Codes:**
- 200: Success
- 400: Invalid ruleset format or validation errors
- 500: Internal server error

---

### 3. Upload Ruleset (File Upload)
**POST /api/ruleset/upload-file**

Upload and activate a new ruleset from file.

**Request:** Multipart form data with file field

**Response:**
```json
{
  "message": "Ruleset loaded successfully",
  "sha": "abc123...",
  "rules_count": 5
}
```

---

### 4. Single Event Evaluation
**POST /api/evaluate**

Evaluate a single payload against the currently loaded ruleset.

**Request Body:**
```json
{
  "payload": {
    "customer_tier": "premium",
    "order_total": 350.00,
    "item_count": 5
  }
}
```

**Response:**
```json
{
  "rule_id": "premium_customer_high_value",
  "outcome": {
    "decision": "approve_discount",
    "discount_percent": 15,
    "reason": "Premium customer qualifies for high-value discount"
  },
  "matched_conditions": [
    "customer_tier equals premium",
    "order_total >= 300"
  ],
  "elapsed_us": 1250,
  "timestamp": 1704067200,
  "rule_sha": "abc123..."
}
```

**Status Codes:**
- 200: Success (includes null response if no rules match)
- 400: Invalid payload format
- 404: No ruleset loaded
- 500: Evaluation error

---

### 5. Batch Event Evaluation
**POST /api/evaluate-batch**

Evaluate multiple events in a single request for improved performance.

**Request Body:**
```json
{
  "events": [
    {
      "customer_tier": "premium",
      "order_total": 350.00
    },
    {
      "transaction_amount": 25000.00,
      "risk_score": "high"
    }
  ]
}
```

**Response:**
```json
{
  "decisions": [
    {
      "rule_id": "premium_customer_high_value",
      "outcome": {
        "decision": "approve_discount",
        "discount_percent": 15
      },
      "matched_conditions": ["customer_tier equals premium"],
      "elapsed_us": 1200,
      "timestamp": 1704067200,
      "rule_sha": "abc123..."
    },
    {
      "rule_id": "high_value_transaction_review",
      "outcome": {
        "decision": "require_manual_review",
        "escalation_level": "tier_2"
      },
      "matched_conditions": ["transaction_amount >= 20000"],
      "elapsed_us": 980,
      "timestamp": 1704067201,
      "rule_sha": "abc123..."
    }
  ]
}
```

---

### 6. Ruleset Status
**GET /api/ruleset/status**

Get information about the currently loaded ruleset.

**Response:**
```json
{
  "loaded": true,
  "sha": "abc123...",
  "rules_count": 12,
  "last_modified": "2024-01-01T12:00:00Z"
}
```

**When no ruleset is loaded:**
```json
{
  "loaded": false,
  "sha": null,
  "rules_count": 0,
  "last_modified": null
}
```

---

### 7. Audit Log
**GET /api/audit/log**

Retrieve audit log entries showing rule changes and decisions.

**Query Parameters:**
- `limit` (optional): Number of entries to return (default: 100, max: 1000)
- `since` (optional): ISO 8601 timestamp to filter entries after

**Response:**
```json
{
  "entries": [
    {
      "id": 1,
      "rule_sha": "abc123...",
      "author": "system",
      "timestamp": "2024-01-01T12:00:00Z",
      "prompt_sha": null,
      "llm_model": null,
      "diff_url": null,
      "content": "Ruleset uploaded via API",
      "type": "ruleset_change"
    },
    {
      "id": 2,
      "rule_sha": "abc123...",
      "decision_data": {
        "rule_id": "premium_customer_high_value",
        "outcome": {"decision": "approve_discount"}
      },
      "timestamp": "2024-01-01T12:01:00Z",
      "type": "decision"
    }
  ],
  "total": 2,
  "limit": 100,
  "since": null
}
```

---

### 8. Health Check
**GET /health**

System health and status endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "features": {
    "rule_engine": true,
    "audit_logging": true,
    "llm_integration": true,
    "batch_processing": true
  }
}
```

---

## Rule DSL Specification

### Ruleset Structure
```yaml
version: "1.0"
rules:
  - id: "rule_identifier"
    description: "Human-readable description"
    tags: ["category", "business_domain"]
    when:
      # Condition specification
    then:
      outcome:
        # Decision output
```

### Condition Types

#### 1. Equals Condition
```yaml
when:
  type: "equals"
  field: "customer_tier"
  value: "premium"
```

#### 2. Greater Than / Less Than
```yaml
when:
  type: "greater_than"
  field: "order_total"
  value: 300.00
```

```yaml
when:
  type: "less_than"
  field: "risk_score"
  value: 0.5
```

#### 3. Range Condition
```yaml
when:
  type: "range"
  field: "credit_score"
  min: 700
  max: 850
```

#### 4. Contains Condition
```yaml
when:
  type: "contains"
  field: "customer_tags"
  value: "vip"
```

#### 5. Logical Operators
```yaml
when:
  type: "and"
  conditions:
    - type: "equals"
      field: "customer_tier"
      value: "premium"
    - type: "greater_than"
      field: "order_total"
      value: 300
```

```yaml
when:
  type: "or"
  conditions:
    - type: "equals"
      field: "customer_tier"
      value: "premium"
    - type: "equals"
      field: "customer_tier"
      value: "gold"
```

### Outcome Structure
```yaml
then:
  outcome:
    decision: "approve_discount"
    discount_percent: 15
    reason: "Premium customer qualifies for discount"
    priority: "high"
    escalation_level: "tier_1"
    processing_time_hours: 24
```

---

## Business Domain Examples

### E-commerce Rules
```yaml
version: "1.0"
rules:
  - id: "premium_customer_discount"
    description: "Premium customers get 15% discount on orders over $300"
    tags: ["ecommerce", "discount", "premium"]
    when:
      type: "and"
      conditions:
        - type: "equals"
          field: "customer_tier"
          value: "premium"
        - type: "greater_than_equal"
          field: "order_total"
          value: 300
    then:
      outcome:
        decision: "approve_discount"
        discount_percent: 15
        reason: "Premium customer high-value order discount"
```

### Financial Risk Assessment
```yaml
  - id: "high_value_transaction_review"
    description: "Transactions over $20,000 require manual review"
    tags: ["finance", "risk", "compliance"]
    when:
      type: "greater_than_equal"
      field: "transaction_amount"
      value: 20000
    then:
      outcome:
        decision: "require_manual_review"
        escalation_level: "tier_2"
        review_deadline_hours: 4
```

### Insurance Claims Processing
```yaml
  - id: "auto_approve_minor_claims"
    description: "Auto-approve small claims for good customers"
    tags: ["insurance", "claims", "automation"]
    when:
      type: "and"
      conditions:
        - type: "less_than"
          field: "claim_amount"
          value: 1000
        - type: "equals"
          field: "customer_fraud_history"
          value: false
        - type: "less_than"
          field: "claims_last_12_months"
          value: 3
    then:
      outcome:
        decision: "auto_approve"
        processing_time_hours: 2
        payment_method: "direct_deposit"
```

---

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Rule validation failed",
    "details": [
      "Rule 'invalid_rule' missing required field 'then'",
      "Condition type 'unknown_type' not supported"
    ]
  }
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Rule validation failures
- `EVALUATION_ERROR`: Runtime evaluation errors
- `NO_RULESET_LOADED`: No active ruleset for evaluation
- `INVALID_PAYLOAD`: Malformed request payload
- `INTERNAL_ERROR`: Server-side processing errors

---

## Performance Considerations

### Evaluation Performance
- Single event evaluation: ~1-5ms typical latency
- Batch evaluation: Optimized for throughput with parallel processing
- Rule complexity: Linear performance with condition count
- Memory usage: Constant memory per evaluation

### Scalability
- Stateless design enables horizontal scaling
- In-memory rule storage for optimal performance
- Audit logging designed for high-volume scenarios
- Batch endpoints reduce HTTP overhead

### Best Practices
1. Use batch evaluation for multiple events
2. Keep rule conditions simple and focused
3. Utilize rule tags for organization and filtering
4. Monitor audit logs for performance insights
5. Validate rulesets before deployment

---

## Integration Examples

### Python Client Example
```python
import requests

# Upload ruleset
ruleset_yaml = """
version: "1.0"
rules:
  - id: "example_rule"
    when:
      type: "equals"
      field: "status"
      value: "active"
    then:
      outcome:
        decision: "approve"
"""

response = requests.post(
    "http://localhost:5000/api/ruleset/upload",
    json={"content": ruleset_yaml, "format": "yaml"}
)

# Evaluate payload
payload = {"status": "active", "amount": 100}
response = requests.post(
    "http://localhost:5000/api/evaluate",
    json={"payload": payload}
)

decision = response.json()
print(f"Decision: {decision['outcome']['decision']}")
```

### JavaScript Client Example
```javascript
// Upload ruleset
const ruleset = {
  content: `
version: "1.0"
rules:
  - id: "js_example"
    when:
      type: "greater_than"
      field: "score"
      value: 80
    then:
      outcome:
        decision: "pass"
  `,
  format: "yaml"
};

const uploadResponse = await fetch('/api/ruleset/upload', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(ruleset)
});

// Evaluate payload
const evaluation = await fetch('/api/evaluate', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    payload: {score: 85, category: "test"}
  })
});

const result = await evaluation.json();
console.log('Rule decision:', result.outcome.decision);
```

---

## Rate Limiting and Quotas

Currently, no rate limiting is implemented. For production deployments, consider:
- Request rate limiting per client
- Payload size restrictions
- Audit log retention policies
- Concurrent evaluation limits

---

## Monitoring and Observability

### Metrics Available
- Rule evaluation latency
- Rule match rates
- Audit log entry counts
- Error rates by endpoint
- Ruleset change frequency

### Logging
- Structured JSON logging
- Request/response tracking
- Rule evaluation traces
- Error stack traces
- Performance metrics

---

## Security Considerations

### Current Implementation
- No authentication/authorization
- Input validation on all endpoints
- Safe rule evaluation (no code execution)
- Audit trail for all changes

### Production Recommendations
- Implement API authentication
- Add authorization controls
- Enable HTTPS/TLS
- Input sanitization
- Rate limiting
- Access logging