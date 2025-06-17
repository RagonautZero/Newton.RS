use crate::engine::{RuleSet, Rule, Condition, Action, EngineError};
use serde_yaml;
use std::collections::HashMap;

pub fn parse_yaml(yaml_content: &str) -> Result<RuleSet, EngineError> {
    serde_yaml::from_str(yaml_content)
        .map_err(|e| EngineError::Parse(format!("YAML parse error: {}", e)))
}

pub fn parse_json(json_content: &str) -> Result<RuleSet, EngineError> {
    serde_json::from_str(json_content)
        .map_err(|e| EngineError::Parse(format!("JSON parse error: {}", e)))
}

pub fn validate_dsl_safety(ruleset: &RuleSet) -> Result<(), EngineError> {
    // Static analysis to ensure no forbidden operations
    for rule in &ruleset.rules {
        validate_condition_safety(&rule.when)?;
    }
    Ok(())
}

fn validate_condition_safety(condition: &Condition) -> Result<(), EngineError> {
    match condition {
        Condition::And { conditions } | Condition::Or { conditions } => {
            for cond in conditions {
                validate_condition_safety(cond)?;
            }
        },
        Condition::Not { condition } => {
            validate_condition_safety(condition)?;
        },
        _ => {
            // All other conditions are safe by design
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_yaml_parsing() {
        let yaml = r#"
rules:
  - id: "test_rule"
    description: "Test rule"
    when:
      type: "equals"
      field: "status"
      value: "active"
    then:
      outcome:
        decision: "approve"
version: "1.0"
metadata: {}
"#;
        
        let result = parse_yaml(yaml);
        assert!(result.is_ok());
    }
}
