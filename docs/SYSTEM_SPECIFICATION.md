# Newton.RS System Specification

## System Overview

Newton.RS is a deterministic rule engine designed for auditable business decision-making with integrated LLM capabilities. The system provides a robust framework for defining, validating, and executing business rules while maintaining complete audit trails and supporting AI-assisted rule generation.


## Architecture

### Core Components

#### 1. Rule Engine Core (`logicbridge/core.py`)
- **Technology**: Python wrapper around Rust engine
- **Responsibilities**:
  - Rule parsing and validation
  - Deterministic rule evaluation
  - SHA-based rule versioning
  - Performance optimization

#### 2. REST API Layer (`logicbridge/api.py`)
- **Technology**: FastAPI framework
- **Port**: 5000
- **Features**:
  - Rule upload and management
  - Single and batch evaluation endpoints
  - Audit log access
  - Health monitoring
  - Web interface serving

#### 3. LLM Integration (`logicbridge/llm_generator.py`)
- **Supported Providers**: OpenAI GPT-4o, Ollama, Mock
- **Capabilities**:
  - Natural language to rule conversion
  - Business scenario understanding
  - Rule generation from user stories
  - Validation and safety checks

#### 4. Audit System (`logicbridge/audit.py`)
- **Database**: SQLite with PostgreSQL support
- **Features**:
  - Rule change tracking
  - Decision logging
  - SHA-based versioning
  - Diff generation
  - Performance metrics

#### 5. Validation Engine (`logicbridge/validation.py`)
- **Schema Validation**: JSON Schema enforcement
- **Safety Checks**: Prevents unsafe operations
- **Determinism Verification**: Ensures consistent outcomes

### System Flow

```
User Request → FastAPI → Rule Engine → Decision + Audit Log
     ↓              ↓         ↓              ↓
Web Interface → Validation → Evaluation → Database Storage
     ↓              ↓         ↓              ↓
LLM Generator → Rule DSL → Deterministic → Versioned History
```

## Rule Definition Language (DSL)

### Syntax Specification

LogicBridge uses a declarative YAML/JSON-based DSL for rule definitions:

```yaml
version: "1.0"
rules:
  - id: "unique_rule_identifier"
    description: "Human-readable rule description"
    tags: ["domain", "category", "priority"]
    when:
      # Condition specification
    then:
      outcome:
        # Decision output structure
```

### Condition Types

#### Simple Conditions
- `equals`: Exact value matching
- `greater_than`: Numeric comparison (>)
- `greater_than_equal`: Numeric comparison (>=)
- `less_than`: Numeric comparison (<)
- `less_than_equal`: Numeric comparison (<=)
- `contains`: Array/string containment
- `starts_with`: String prefix matching
- `ends_with`: String suffix matching
- `range`: Numeric range validation

#### Logical Operators
- `and`: All conditions must be true
- `or`: Any condition must be true
- `not`: Negation of condition

#### Complex Structures
```yaml
when:
  type: "and"
  conditions:
    - type: "equals"
      field: "customer.tier"
      value: "premium"
    - type: "or"
      conditions:
        - type: "greater_than"
          field: "order.total"
          value: 500
        - type: "contains"
          field: "order.items"
          value: "priority_item"
```

### Field Path Resolution
- Dot notation: `customer.profile.tier`
- Array indexing: `items[0].price`
- Nested objects: `metadata.flags.vip_status`

## Business Domain Support

### E-commerce Rules
```yaml
# Customer tier-based discounts
# Bulk order processing
# Inventory management
# Shipping calculations
# Loyalty program benefits
```

### Financial Services
```yaml
# Risk assessment
# Fraud detection
# Transaction limits
# KYC compliance
# Credit scoring
```

### Insurance Claims
```yaml
# Auto-approval workflows
# Escalation procedures
# Coverage validation
# Premium calculations
# Risk assessment
```

### Lending and Credit
```yaml
# Application processing
# Credit line management
# Interest rate determination
# Collateral evaluation
# Default risk assessment
```

## Performance Characteristics

### Evaluation Performance
- **Single Rule**: 1-5ms typical latency
- **Complex Rules**: 5-15ms with multiple conditions
- **Batch Processing**: 100+ evaluations/second
- **Memory Usage**: <10MB for typical rulesets

### Scalability Metrics
- **Rules per Ruleset**: 1,000+ rules supported
- **Concurrent Evaluations**: Limited by available CPU cores
- **Audit Log**: Millions of entries with SQLite/PostgreSQL
- **Rule Complexity**: No practical depth limits

### Optimization Features
- In-memory rule compilation
- Lazy evaluation for performance
- Batch processing for throughput
- Parallel condition evaluation

## Security Model

### Current Implementation
- **Input Validation**: All API inputs validated
- **Safe Evaluation**: No code execution, only data comparison
- **Audit Trail**: Complete change history
- **Deterministic**: Consistent outcomes prevent manipulation

### Production Security Requirements
- API authentication and authorization
- TLS/HTTPS encryption
- Input sanitization and validation
- Rate limiting and DDoS protection
- Role-based access control

## Data Storage

### Audit Database Schema
```sql
-- Rule changes and versioning
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    rule_sha VARCHAR(64) NOT NULL,
    author VARCHAR(255) NOT NULL,
    timestamp DATETIME NOT NULL,
    prompt_sha VARCHAR(64),
    llm_model VARCHAR(100),
    diff_url TEXT,
    content TEXT NOT NULL
);

-- Decision tracking
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    rule_sha VARCHAR(64) NOT NULL,
    decision_data TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    elapsed_us INTEGER NOT NULL
);
```

### Rule Storage
- **Format**: YAML/JSON in memory
- **Versioning**: SHA-256 hashing
- **Persistence**: File-based or database storage
- **Validation**: JSON Schema enforcement

## LLM Integration Specification

### Provider Support

#### OpenAI Integration
- **Model**: GPT-4o (latest available)
- **Authentication**: API key via environment variable
- **Features**: Natural language rule generation
- **Response Format**: Structured JSON output

#### Ollama Integration
- **Deployment**: Local server (localhost:11434)
- **Models**: Llama2, CodeLlama, Mistral
- **Benefits**: Private deployment, no external dependencies

#### Mock Provider
- **Purpose**: Testing and development
- **Features**: Deterministic rule generation
- **Use Cases**: CI/CD, unit testing, demonstrations

### Rule Generation Process
1. **Story Analysis**: Parse user requirements
2. **Rule Synthesis**: Generate appropriate conditions
3. **Validation**: Ensure rule safety and correctness
4. **Metadata Addition**: Add generation timestamps and provenance

## Deployment Architecture

### Container Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "main.py"]
```

### Environment Configuration
```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/db

# Optional LLM Integration
OPENAI_API_KEY=sk-...
OLLAMA_URL=http://localhost:11434

# Server Configuration
HOST=0.0.0.0
PORT=5000
LOG_LEVEL=INFO
```

### Resource Requirements
- **CPU**: 1-2 cores for typical workloads
- **Memory**: 512MB-1GB depending on ruleset size
- **Storage**: 100MB for application + audit log storage
- **Network**: HTTP/HTTPS on port 5000

## Monitoring and Observability

### Health Checks
- **Endpoint**: `/health`
- **Checks**: Database connectivity, rule engine status
- **Response Time**: <100ms typical

### Metrics Collection
- Rule evaluation latency
- Request/response volumes
- Error rates by endpoint
- Ruleset change frequency
- LLM generation success rates

### Logging Strategy
- Structured JSON logging
- Request correlation IDs
- Performance timings
- Error stack traces
- Audit event logging

## Testing Strategy

### Unit Testing
- Rule evaluation correctness
- Condition type validation
- API endpoint functionality
- LLM integration mocking

### Integration Testing
- End-to-end rule workflows
- Database connectivity
- External LLM provider integration
- Performance benchmarking

### Business Scenario Testing
- Real-world rule validation
- Domain-specific use cases
- Edge case handling
- Error condition testing

## Configuration Management

### Rule Configuration
```yaml
# Application settings
app:
  host: "0.0.0.0"
  port: 5000
  debug: false

# Database settings
database:
  url: "${DATABASE_URL}"
  pool_size: 10

# LLM settings
llm:
  default_provider: "openai"
  fallback_provider: "mock"
  timeout_seconds: 30
```

### Feature Flags
- LLM integration enable/disable
- Audit logging verbosity
- Performance monitoring
- Development mode toggles

## Error Handling

### Error Categories
1. **Validation Errors**: Rule syntax, schema violations
2. **Evaluation Errors**: Runtime failures, data issues
3. **System Errors**: Database connectivity, resource limits
4. **LLM Errors**: API failures, timeout issues

### Error Response Format
```json
{
  "error": {
    "code": "ERROR_TYPE",
    "message": "Human-readable description",
    "details": ["Specific error details"],
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_123456"
  }
}
```

## Extensibility

### Plugin Architecture
- Custom condition types
- External data source integration
- Custom outcome processors
- Third-party LLM providers

### API Versioning
- Version-specific endpoints
- Backward compatibility
- Migration pathways
- Deprecation strategies

## Compliance and Governance

### Audit Requirements
- Complete decision trail
- Rule change versioning
- Author attribution
- Timestamp accuracy

### Regulatory Considerations
- Financial services compliance
- Healthcare data protection
- Privacy regulations
- Cross-border data transfer

## Migration and Upgrade

### Version Compatibility
- Rule DSL backward compatibility
- API endpoint stability
- Database schema evolution
- Configuration migration

### Upgrade Procedures
1. Backup current rulesets
2. Test new version compatibility
3. Migrate configuration
4. Validate rule behavior
5. Update monitoring dashboards