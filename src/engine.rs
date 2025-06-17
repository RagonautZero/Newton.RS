use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};
use thiserror::Error;
use sha2::{Sha256, Digest};

#[derive(Error, Debug)]
pub enum EngineError {
    #[error("Rule validation error: {0}")]
    RuleValidation(String),
    #[error("Execution error: {0}")]
    Execution(String),
    #[error("Parse error: {0}")]
    Parse(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Rule {
    pub id: String,
    pub description: Option<String>,
    pub severity: Option<String>,
    pub tags: Vec<String>,
    pub when: Condition,
    pub then: Action,
    #[serde(default)]
    pub generated_by_llm: bool,
    pub prompt_sha: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RuleSet {
    pub rules: Vec<Rule>,
    pub version: String,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum Condition {
    #[serde(rename = "and")]
    And { conditions: Vec<Condition> },
    #[serde(rename = "or")]
    Or { conditions: Vec<Condition> },
    #[serde(rename = "not")]
    Not { condition: Box<Condition> },
    #[serde(rename = "equals")]
    Equals { field: String, value: serde_json::Value },
    #[serde(rename = "greater_than")]
    GreaterThan { field: String, value: f64 },
    #[serde(rename = "less_than")]
    LessThan { field: String, value: f64 },
    #[serde(rename = "contains")]
    Contains { field: String, value: String },
    #[serde(rename = "in")]
    In { field: String, values: Vec<serde_json::Value> },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Action {
    pub outcome: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Decision {
    pub rule_id: String,
    pub outcome: HashMap<String, serde_json::Value>,
    pub matched_conditions: Vec<String>,
    pub elapsed_us: u64,
    pub timestamp: u64,
    pub rule_sha: String,
}

pub struct RuleEngine {
    ruleset: Option<RuleSet>,
    ruleset_sha: Option<String>,
}

impl RuleEngine {
    pub fn new() -> Self {
        Self {
            ruleset: None,
            ruleset_sha: None,
        }
    }

    pub fn load_ruleset(&mut self, ruleset: RuleSet) -> Result<(), EngineError> {
        // Validate ruleset
        self.validate_ruleset(&ruleset)?;
        
        // Calculate SHA
        let canonical_json = serde_json::to_string(&ruleset)
            .map_err(|e| EngineError::Parse(e.to_string()))?;
        let mut hasher = Sha256::new();
        hasher.update(canonical_json.as_bytes());
        let sha = format!("{:x}", hasher.finalize());
        
        self.ruleset = Some(ruleset);
        self.ruleset_sha = Some(sha);
        Ok(())
    }

    pub fn get_ruleset_sha(&self) -> Option<&String> {
        self.ruleset_sha.as_ref()
    }

    fn validate_ruleset(&self, ruleset: &RuleSet) -> Result<(), EngineError> {
        // Check for duplicate rule IDs
        let mut ids = std::collections::HashSet::new();
        for rule in &ruleset.rules {
            if !ids.insert(&rule.id) {
                return Err(EngineError::RuleValidation(
                    format!("Duplicate rule ID: {}", rule.id)
                ));
            }
        }
        Ok(())
    }

    pub fn evaluate(&self, payload: &HashMap<String, serde_json::Value>) -> Result<Option<Decision>, EngineError> {
        let ruleset = self.ruleset.as_ref()
            .ok_or_else(|| EngineError::Execution("No ruleset loaded".to_string()))?;
        
        let start_time = SystemTime::now();
        
        for rule in &ruleset.rules {
            if self.evaluate_condition(&rule.when, payload)? {
                let elapsed = start_time.elapsed()
                    .map_err(|e| EngineError::Execution(e.to_string()))?;
                
                let decision = Decision {
                    rule_id: rule.id.clone(),
                    outcome: rule.then.outcome.clone(),
                    matched_conditions: vec![rule.id.clone()], // Simplified
                    elapsed_us: elapsed.as_micros() as u64,
                    timestamp: SystemTime::now()
                        .duration_since(UNIX_EPOCH)
                        .unwrap()
                        .as_secs(),
                    rule_sha: self.ruleset_sha.clone().unwrap_or_default(),
                };
                
                return Ok(Some(decision));
            }
        }
        
        Ok(None)
    }

    pub fn evaluate_many(&self, events: &[HashMap<String, serde_json::Value>]) -> Result<Vec<Option<Decision>>, EngineError> {
        events.iter()
            .map(|event| self.evaluate(event))
            .collect()
    }

    fn evaluate_condition(&self, condition: &Condition, payload: &HashMap<String, serde_json::Value>) -> Result<bool, EngineError> {
        match condition {
            Condition::And { conditions } => {
                for cond in conditions {
                    if !self.evaluate_condition(cond, payload)? {
                        return Ok(false);
                    }
                }
                Ok(true)
            },
            Condition::Or { conditions } => {
                for cond in conditions {
                    if self.evaluate_condition(cond, payload)? {
                        return Ok(true);
                    }
                }
                Ok(false)
            },
            Condition::Not { condition } => {
                Ok(!self.evaluate_condition(condition, payload)?)
            },
            Condition::Equals { field, value } => {
                Ok(payload.get(field) == Some(value))
            },
            Condition::GreaterThan { field, value } => {
                if let Some(field_value) = payload.get(field) {
                    if let Some(num) = field_value.as_f64() {
                        return Ok(num > *value);
                    }
                }
                Ok(false)
            },
            Condition::LessThan { field, value } => {
                if let Some(field_value) = payload.get(field) {
                    if let Some(num) = field_value.as_f64() {
                        return Ok(num < *value);
                    }
                }
                Ok(false)
            },
            Condition::Contains { field, value } => {
                if let Some(field_value) = payload.get(field) {
                    if let Some(str_val) = field_value.as_str() {
                        return Ok(str_val.contains(value));
                    }
                }
                Ok(false)
            },
            Condition::In { field, values } => {
                if let Some(field_value) = payload.get(field) {
                    return Ok(values.contains(field_value));
                }
                Ok(false)
            },
        }
    }
}

impl Default for RuleEngine {
    fn default() -> Self {
        Self::new()
    }
}
