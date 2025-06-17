// LogicBridge Rule Engine Frontend Application

class LogicBridgeApp {
    constructor() {
        this.apiBase = '/api';
        this.currentRulesetSha = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadStatus();
    }

    setupEventListeners() {
        // Ruleset upload form
        document.getElementById('ruleset-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.uploadRuleset();
        });

        // File input change
        document.getElementById('rulesetFile').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.loadFileContent(e.target.files[0]);
            }
        });

        // Evaluation form
        document.getElementById('evaluate-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.evaluatePayload();
        });

        // Tab change events
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                if (e.target.id === 'audit-tab') {
                    this.loadAuditLog();
                }
            });
        });
    }

    async loadFileContent(file) {
        try {
            const content = await this.readFileAsText(file);
            document.getElementById('rulesetContent').value = content;
            
            // Auto-detect format
            const format = file.name.endsWith('.json') ? 'json' : 'yaml';
            document.getElementById('rulesetFormat').value = format;
        } catch (error) {
            this.showAlert('danger', `Error reading file: ${error.message}`);
        }
    }

    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }

    async uploadRuleset() {
        const content = document.getElementById('rulesetContent').value.trim();
        const format = document.getElementById('rulesetFormat').value;
        const resultDiv = document.getElementById('ruleset-result');

        if (!content) {
            this.showAlert('warning', 'Please provide ruleset content or select a file.');
            return;
        }

        this.showLoading(resultDiv);

        try {
            const response = await fetch(`${this.apiBase}/ruleset/upload`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    format: format
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.currentRulesetSha = result.rule_sha;
                resultDiv.innerHTML = `
                    <div class="alert alert-success fade-in">
                        <i class="fas fa-check-circle me-2"></i>
                        <strong>Success!</strong> Ruleset loaded successfully.
                        <br><small class="rule-sha">SHA: ${result.rule_sha}</small>
                    </div>
                `;
                this.loadStatus(); // Refresh status
            } else {
                throw new Error(result.detail || 'Upload failed');
            }
        } catch (error) {
            resultDiv.innerHTML = `
                <div class="alert alert-danger fade-in">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    <strong>Error:</strong> ${error.message}
                </div>
            `;
        }
    }

    async evaluatePayload() {
        const payloadContent = document.getElementById('payloadContent').value.trim();
        const batchMode = document.getElementById('batchMode').checked;
        const resultDiv = document.getElementById('evaluate-result');

        if (!payloadContent) {
            this.showAlert('warning', 'Please provide a payload to evaluate.');
            return;
        }

        if (!this.currentRulesetSha) {
            resultDiv.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    No ruleset loaded. Please upload a ruleset first.
                </div>
            `;
            return;
        }

        this.showLoading(resultDiv);

        try {
            const payload = JSON.parse(payloadContent);
            
            let endpoint, requestBody;
            if (batchMode) {
                endpoint = `${this.apiBase}/evaluate-batch`;
                requestBody = { events: Array.isArray(payload) ? payload : [payload] };
            } else {
                endpoint = `${this.apiBase}/evaluate`;
                requestBody = { payload: payload };
            }

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            const result = await response.json();

            if (response.ok) {
                this.displayEvaluationResult(result, batchMode, resultDiv);
            } else {
                throw new Error(result.detail || 'Evaluation failed');
            }
        } catch (error) {
            if (error instanceof SyntaxError) {
                resultDiv.innerHTML = `
                    <div class="alert alert-danger fade-in">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        <strong>JSON Parse Error:</strong> Invalid JSON format in payload.
                    </div>
                `;
            } else {
                resultDiv.innerHTML = `
                    <div class="alert alert-danger fade-in">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        <strong>Error:</strong> ${error.message}
                    </div>
                `;
            }
        }
    }

    displayEvaluationResult(result, batchMode, container) {
        let html = '<div class="fade-in">';

        if (batchMode) {
            html += '<h6><i class="fas fa-list me-2"></i>Batch Evaluation Results</h6>';
            
            if (result.decisions && result.decisions.length > 0) {
                result.decisions.forEach((decision, index) => {
                    html += this.formatDecisionCard(decision, `Event ${index + 1}`);
                });
            } else {
                html += '<div class="alert alert-info">No decisions returned for batch evaluation.</div>';
            }
        } else {
            html += '<h6><i class="fas fa-gavel me-2"></i>Evaluation Result</h6>';
            html += this.formatDecisionCard(result, 'Single Evaluation');
        }

        html += '</div>';
        container.innerHTML = html;
    }

    formatDecisionCard(decision, title) {
        if (!decision) {
            return `
                <div class="card decision-card no-match mb-3">
                    <div class="card-body">
                        <h6 class="card-title">
                            <i class="fas fa-times-circle text-muted me-2"></i>
                            ${title}
                        </h6>
                        <p class="text-muted mb-0">No rules matched the provided payload.</p>
                    </div>
                </div>
            `;
        }

        return `
            <div class="card decision-card mb-3">
                <div class="card-body">
                    <h6 class="card-title">
                        <i class="fas fa-check-circle text-success me-2"></i>
                        ${title}
                    </h6>
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Rule ID:</strong> <code>${decision.rule_id}</code><br>
                            <strong>Performance:</strong> 
                            <span class="performance-badge">${decision.elapsed_us}μs</span><br>
                            <strong>Rule SHA:</strong> 
                            <span class="rule-sha">${decision.rule_sha.substring(0, 12)}...</span>
                        </div>
                        <div class="col-md-6">
                            <strong>Outcome:</strong>
                            <div class="json-display mt-1">
${JSON.stringify(decision.outcome, null, 2)}
                            </div>
                        </div>
                    </div>
                    ${decision.matched_conditions && decision.matched_conditions.length > 0 ? 
                        `<div class="mt-2">
                            <strong>Matched Conditions:</strong> 
                            ${decision.matched_conditions.map(c => `<code class="me-1">${c}</code>`).join('')}
                        </div>` : ''
                    }
                </div>
            </div>
        `;
    }

    async loadStatus() {
        try {
            const response = await fetch(`${this.apiBase}/ruleset/status`);
            const status = await response.json();
            
            const statusContent = document.getElementById('status-content');
            
            if (status.loaded) {
                this.currentRulesetSha = status.rule_sha;
                statusContent.innerHTML = `
                    <div class="row">
                        <div class="col-md-4">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-check-circle text-success me-2"></i>
                                <span class="status-badge status-loaded">Ruleset Loaded</span>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <small class="text-muted">Rule SHA:</small><br>
                            <span class="rule-sha">${status.rule_sha}</span>
                        </div>
                        <div class="col-md-4">
                            <small class="text-muted">Last Updated:</small><br>
                            <span>${status.timestamp ? new Date(status.timestamp).toLocaleString() : 'Unknown'}</span>
                        </div>
                    </div>
                `;
            } else {
                statusContent.innerHTML = `
                    <div class="d-flex align-items-center">
                        <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                        <span class="status-badge status-empty">No Ruleset Loaded</span>
                        <span class="ms-3 text-muted">Upload a ruleset to get started</span>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Failed to load status:', error);
            document.getElementById('status-content').innerHTML = `
                <div class="alert alert-danger mb-0">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Failed to load engine status
                </div>
            `;
        }
    }

    async loadAuditLog() {
        const auditContent = document.getElementById('audit-content');
        this.showLoading(auditContent);

        try {
            const response = await fetch(`${this.apiBase}/audit/log?limit=50`);
            const entries = await response.json();

            if (entries.length === 0) {
                auditContent.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        No audit log entries found.
                    </div>
                `;
                return;
            }

            let html = '<div class="fade-in">';
            entries.forEach(entry => {
                html += `
                    <div class="audit-entry">
                        <div class="row">
                            <div class="col-md-8">
                                <h6 class="mb-1">
                                    <i class="fas fa-code-branch me-2"></i>
                                    Rule Change by ${entry.author}
                                </h6>
                                <small class="text-muted">
                                    <i class="fas fa-clock me-1"></i>
                                    ${new Date(entry.timestamp).toLocaleString()}
                                </small>
                                ${entry.llm_model ? 
                                    `<br><small class="text-info">
                                        <i class="fas fa-robot me-1"></i>
                                        Generated by ${entry.llm_model}
                                    </small>` : ''
                                }
                            </div>
                            <div class="col-md-4 text-end">
                                <span class="rule-sha">${entry.rule_sha.substring(0, 12)}...</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            
            auditContent.innerHTML = html;
        } catch (error) {
            auditContent.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Failed to load audit log: ${error.message}
                </div>
            `;
        }
    }

    showLoading(container) {
        container.innerHTML = `
            <div class="d-flex justify-content-center p-3">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
    }

    showAlert(type, message) {
        // This could be enhanced to show toast notifications
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

// Sample data functions
function loadSampleRuleset() {
    const sampleRuleset = `rules:
  - id: "premium_customer_discount"
    description: "Premium customers get 10% discount on orders over $100"
    severity: "medium"
    tags: ["discount", "premium"]
    when:
      type: "and"
      conditions:
        - type: "equals"
          field: "customer_tier"
          value: "premium"
        - type: "greater_than"
          field: "order_total"
          value: 100
    then:
      outcome:
        decision: "approve_discount"
        discount_percent: 10
        reason: "Premium customer discount"

version: "1.0"
metadata:
  description: "Sample discount rules"`;

    document.getElementById('rulesetContent').value = sampleRuleset;
    document.getElementById('rulesetFormat').value = 'yaml';
}

function loadSamplePayload() {
    const samplePayload = `{
  "customer_tier": "premium",
  "order_total": 150,
  "item_count": 3,
  "is_first_order": false
}`;

    document.getElementById('payloadContent').value = samplePayload;
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.logicBridgeApp = new LogicBridgeApp();
});

// Global functions for buttons
window.loadAuditLog = () => {
    if (window.logicBridgeApp) {
        window.logicBridgeApp.loadAuditLog();
    }
};

window.loadSampleRuleset = loadSampleRuleset;
window.loadSamplePayload = loadSamplePayload;
