# Newton.RS API Testing Guide


## Quick Start Testing

### 1. Basic Health Check
```bash
curl -X GET http://localhost:5000/health
```

Expected Response:
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

### 2. Upload E-commerce Ruleset
```bash
curl -X POST http://localhost:5000/api/ruleset/upload \
  -H "Content-Type: application/json" \
  -d '{
    "content": "version: \"1.0\"\nrules:\n  - id: \"premium_discount\"\n    description: \"Premium customer discount\"\n    when:\n      type: \"and\"\n      conditions:\n        - type: \"equals\"\n          field: \"customer_tier\"\n          value: \"premium\"\n        - type: \"greater_than\"\n          field: \"order_total\"\n          value: 300\n    then:\n      outcome:\n        decision: \"approve_discount\"\n        discount_percent: 15",
    "format": "yaml"
  }'
```

### 3. Test Premium Customer Evaluation
```bash
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "customer_tier": "premium",
      "order_total": 350.00,
      "item_count": 5
    }
  }'
```

Expected Response:
```json
{
  "rule_id": "premium_discount",
  "outcome": {
    "decision": "approve_discount",
    "discount_percent": 15
  },
  "matched_conditions": [
    "customer_tier equals premium",
    "order_total > 300"
  ],
  "elapsed_us": 1250,
  "timestamp": 1704067200,
  "rule_sha": "abc123..."
}
```

## Comprehensive Business Scenario Testing

### E-commerce Scenarios

#### Premium Customer High-Value Order
```bash
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "customer_tier": "premium",
      "order_total": 450.00,
      "customer_id": "CUST_12345",
      "order_items": ["laptop", "mouse", "keyboard"]
    }
  }'
```

#### Bulk Order Processing
```bash
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "item_count": 15,
      "order_total": 280.00,
      "customer_tier": "standard"
    }
  }'
```

#### Loyalty Program Benefits
```bash
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "customer_tenure_years": 5,
      "customer_tier": "gold",
      "order_total": 120.00
    }
  }'
```

### Financial Risk Assessment

#### High-Value Transaction Review
```bash
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "transaction_amount": 25000.00,
      "customer_id": "CUST_001",
      "transaction_type": "wire_transfer",
      "destination_country": "US"
    }
  }'
```

#### Fraud Detection Trigger
```bash
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "transaction_amount": 5000.00,
      "unusual_pattern": true,
      "velocity_score": 0.85,
      "device_fingerprint": "unknown"
    }
  }'
```

### Insurance Claims Processing

#### Auto-Approve Minor Claim
```bash
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "claim_amount": 750.00,
      "customer_fraud_history": false,
      "claims_last_12_months": 1,
      "claim_type": "auto",
      "policy_active": true
    }
  }'
```

#### Specialist Review Required
```bash
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "claim_amount": 15000.00,
      "claim_type": "medical",
      "pre_existing_condition": true,
      "specialist_required": true
    }
  }'
```

### Lending and Credit Decisions

#### Prime Customer Fast-Track
```bash
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "credit_score": 780,
      "annual_income": 150000,
      "debt_to_income_ratio": 0.25,
      "loan_amount": 300000,
      "employment_years": 8
    }
  }'
```

#### Manual Underwriting Required
```bash
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "credit_score": 650,
      "annual_income": 45000,
      "debt_to_income_ratio": 0.45,
      "loan_amount": 250000,
      "self_employed": true
    }
  }'
```

## Batch Processing Testing

### Mixed Business Scenarios
```bash
curl -X POST http://localhost:5000/api/evaluate-batch \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "customer_tier": "premium",
        "order_total": 350.00
      },
      {
        "transaction_amount": 25000.00,
        "risk_score": "high"
      },
      {
        "claim_amount": 750.00,
        "customer_fraud_history": false
      },
      {
        "credit_score": 780,
        "loan_amount": 300000
      }
    ]
  }'
```

Expected Response Structure:
```json
{
  "decisions": [
    {
      "rule_id": "premium_customer_discount",
      "outcome": {"decision": "approve_discount", "discount_percent": 15}
    },
    {
      "rule_id": "high_value_transaction_review",
      "outcome": {"decision": "require_manual_review"}
    },
    {
      "rule_id": "auto_approve_minor_claims",
      "outcome": {"decision": "auto_approve"}
    },
    {
      "rule_id": "prime_customer_fast_track",
      "outcome": {"decision": "approve", "interest_rate": 3.25}
    }
  ]
}
```

## Status and Monitoring Testing

### Ruleset Status Check
```bash
curl -X GET http://localhost:5000/api/ruleset/status
```

### Audit Log Retrieval
```bash
curl -X GET "http://localhost:5000/api/audit/log?limit=50"
```

### Filtered Audit Log
```bash
curl -X GET "http://localhost:5000/api/audit/log?limit=25&since=2024-01-01T00:00:00Z"
```

## Error Condition Testing

### Invalid Ruleset Upload
```bash
curl -X POST http://localhost:5000/api/ruleset/upload \
  -H "Content-Type: application/json" \
  -d '{
    "content": "invalid: yaml: content",
    "format": "yaml"
  }'
```

Expected Error Response:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Rule validation failed",
    "details": ["Invalid YAML syntax"]
  }
}
```

### Evaluation Without Ruleset
```bash
# First ensure no ruleset is loaded, then:
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"test": "data"}
  }'
```

Expected Error Response:
```json
{
  "error": {
    "code": "NO_RULESET_LOADED",
    "message": "No ruleset is currently loaded"
  }
}
```

### Invalid Payload Format
```bash
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"invalid": "request structure"}'
```

## Performance Testing

### Single Evaluation Latency
```bash
time curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "customer_tier": "premium",
      "order_total": 350.00
    }
  }'
```

### Batch Processing Performance
```bash
# Create payload with 100 events
time curl -X POST http://localhost:5000/api/evaluate-batch \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      // Array of 100 test events
    ]
  }'
```

## Advanced Testing Scenarios

### Complex Nested Conditions
```bash
curl -X POST http://localhost:5000/api/ruleset/upload \
  -H "Content-Type: application/json" \
  -d '{
    "content": "version: \"1.0\"\nrules:\n  - id: \"complex_business_rule\"\n    when:\n      type: \"and\"\n      conditions:\n        - type: \"or\"\n          conditions:\n            - type: \"equals\"\n              field: \"customer.tier\"\n              value: \"premium\"\n            - type: \"equals\"\n              field: \"customer.tier\"\n              value: \"gold\"\n        - type: \"and\"\n          conditions:\n            - type: \"greater_than\"\n              field: \"order.total\"\n              value: 200\n            - type: \"less_than\"\n              field: \"order.items\"\n              value: 20\n    then:\n      outcome:\n        decision: \"approve\"\n        priority: \"high\"",
    "format": "yaml"
  }'
```

### Field Path Resolution Testing
```bash
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "customer": {
        "tier": "premium",
        "profile": {
          "vip_status": true,
          "loyalty_years": 5
        }
      },
      "order": {
        "total": 450.00,
        "items": 8,
        "metadata": {
          "priority_shipping": true
        }
      }
    }
  }'
```

## File Upload Testing

### Upload Ruleset via File
```bash
# Create test file first
echo 'version: "1.0"
rules:
  - id: "file_upload_test"
    when:
      type: "equals"
      field: "test"
      value: true
    then:
      outcome:
        decision: "success"' > test_ruleset.yaml

# Upload the file
curl -X POST http://localhost:5000/api/ruleset/upload-file \
  -F "file=@test_ruleset.yaml"
```

## Integration Testing Scripts

### Python Test Client
```python
import requests
import time
import json

base_url = "http://localhost:5000"

def run_integration_tests():
    # Health check
    response = requests.get(f"{base_url}/health")
    assert response.status_code == 200
    print("✓ Health check passed")
    
    # Upload comprehensive ruleset
    with open("examples/comprehensive_business_rules.yml", "r") as f:
        ruleset_content = f.read()
    
    response = requests.post(f"{base_url}/api/ruleset/upload", 
                           json={"content": ruleset_content, "format": "yaml"})
    assert response.status_code == 200
    print("✓ Ruleset upload passed")
    
    # Test various scenarios
    test_cases = [
        {"customer_tier": "premium", "order_total": 350.00},
        {"transaction_amount": 25000.00, "risk_score": "high"},
        {"claim_amount": 750.00, "customer_fraud_history": False},
        {"credit_score": 780, "loan_amount": 300000}
    ]
    
    for i, payload in enumerate(test_cases):
        response = requests.post(f"{base_url}/api/evaluate", 
                               json={"payload": payload})
        assert response.status_code == 200
        result = response.json()
        assert result is not None
        print(f"✓ Test case {i+1} passed: {result['rule_id']}")
    
    print("All integration tests passed!")

if __name__ == "__main__":
    run_integration_tests()
```

### JavaScript Test Client
```javascript
const axios = require('axios');

const baseUrl = 'http://localhost:5000';

async function runTests() {
    try {
        // Health check
        const health = await axios.get(`${baseUrl}/health`);
        console.log('✓ Health check passed');
        
        // Upload test ruleset
        const ruleset = {
            content: `
version: "1.0"
rules:
  - id: "js_test_rule"
    when:
      type: "equals"
      field: "language"
      value: "javascript"
    then:
      outcome:
        decision: "approve"
        framework: "nodejs"
            `,
            format: "yaml"
        };
        
        const upload = await axios.post(`${baseUrl}/api/ruleset/upload`, ruleset);
        console.log('✓ Ruleset upload passed');
        
        // Test evaluation
        const evaluation = await axios.post(`${baseUrl}/api/evaluate`, {
            payload: {
                language: "javascript",
                version: "18.0"
            }
        });
        
        console.log('✓ Evaluation passed:', evaluation.data.outcome);
        console.log('All JavaScript tests passed!');
        
    } catch (error) {
        console.error('Test failed:', error.response?.data || error.message);
    }
}

runTests();
```

## Automated Testing with curl Scripts

### Complete Test Suite
```bash
#!/bin/bash

BASE_URL="http://localhost:5000"

echo "Running LogicBridge API Test Suite..."

# Test 1: Health Check
echo "Test 1: Health Check"
curl -s -X GET "$BASE_URL/health" | jq .status || exit 1
echo "✓ Health check passed"

# Test 2: Upload Comprehensive Ruleset
echo "Test 2: Upload Ruleset"
curl -s -X POST "$BASE_URL/api/ruleset/upload" \
  -H "Content-Type: application/json" \
  -d @examples/comprehensive_business_rules.json | jq .message || exit 1
echo "✓ Ruleset upload passed"

# Test 3-6: Business Scenarios
echo "Test 3: E-commerce Evaluation"
curl -s -X POST "$BASE_URL/api/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"payload":{"customer_tier":"premium","order_total":350}}' | jq .rule_id || exit 1
echo "✓ E-commerce test passed"

echo "Test 4: Financial Risk Evaluation"
curl -s -X POST "$BASE_URL/api/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"payload":{"transaction_amount":25000,"risk_score":"high"}}' | jq .rule_id || exit 1
echo "✓ Financial test passed"

echo "Test 5: Batch Evaluation"
curl -s -X POST "$BASE_URL/api/evaluate-batch" \
  -H "Content-Type: application/json" \
  -d '{"events":[{"customer_tier":"premium","order_total":350},{"claim_amount":750}]}' | jq .decisions || exit 1
echo "✓ Batch test passed"

echo "Test 6: Audit Log"
curl -s -X GET "$BASE_URL/api/audit/log?limit=5" | jq .entries || exit 1
echo "✓ Audit log test passed"

echo "All tests passed successfully!"
```

Make the script executable and run:
```bash
chmod +x test_suite.sh
./test_suite.sh
```