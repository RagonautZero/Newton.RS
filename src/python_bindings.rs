use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;
use crate::engine::{RuleEngine, RuleSet, Decision, EngineError};
use crate::dsl;

#[pyclass]
pub struct PyRuleEngine {
    engine: RuleEngine,
}

#[pyclass]
#[derive(Clone)]
pub struct PyDecision {
    #[pyo3(get)]
    pub rule_id: String,
    #[pyo3(get)]
    pub outcome: HashMap<String, serde_json::Value>,
    #[pyo3(get)]
    pub matched_conditions: Vec<String>,
    #[pyo3(get)]
    pub elapsed_us: u64,
    #[pyo3(get)]
    pub timestamp: u64,
    #[pyo3(get)]
    pub rule_sha: String,
}

#[pyclass]
pub struct PyRuleSet {
    ruleset: RuleSet,
}

impl From<Decision> for PyDecision {
    fn from(decision: Decision) -> Self {
        PyDecision {
            rule_id: decision.rule_id,
            outcome: decision.outcome,
            matched_conditions: decision.matched_conditions,
            elapsed_us: decision.elapsed_us,
            timestamp: decision.timestamp,
            rule_sha: decision.rule_sha,
        }
    }
}

#[pymethods]
impl PyRuleEngine {
    #[new]
    pub fn new() -> Self {
        PyRuleEngine {
            engine: RuleEngine::new(),
        }
    }

    pub fn load_ruleset_from_yaml(&mut self, yaml_content: &str) -> PyResult<()> {
        let ruleset = dsl::parse_yaml(yaml_content)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        
        self.engine.load_ruleset(ruleset)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        Ok(())
    }

    pub fn load_ruleset_from_json(&mut self, json_content: &str) -> PyResult<()> {
        let ruleset = dsl::parse_json(json_content)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        
        self.engine.load_ruleset(ruleset)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        Ok(())
    }

    pub fn evaluate(&self, payload: &PyDict) -> PyResult<Option<PyDecision>> {
        let payload_map = python_dict_to_hashmap(payload)?;
        
        let decision = self.engine.evaluate(&payload_map)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        Ok(decision.map(PyDecision::from))
    }

    pub fn evaluate_many(&self, events: Vec<&PyDict>) -> PyResult<Vec<Option<PyDecision>>> {
        let mut payload_maps = Vec::new();
        for event in events {
            payload_maps.push(python_dict_to_hashmap(event)?);
        }
        
        let decisions = self.engine.evaluate_many(&payload_maps)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        Ok(decisions.into_iter().map(|d| d.map(PyDecision::from)).collect())
    }

    pub fn get_ruleset_sha(&self) -> Option<String> {
        self.engine.get_ruleset_sha().cloned()
    }
}

fn python_dict_to_hashmap(py_dict: &PyDict) -> PyResult<HashMap<String, serde_json::Value>> {
    let mut map = HashMap::new();
    for (key, value) in py_dict.iter() {
        let key_str = key.extract::<String>()?;
        let json_value = python_value_to_json(value)?;
        map.insert(key_str, json_value);
    }
    Ok(map)
}

fn python_value_to_json(value: &PyAny) -> PyResult<serde_json::Value> {
    if value.is_none() {
        Ok(serde_json::Value::Null)
    } else if let Ok(b) = value.extract::<bool>() {
        Ok(serde_json::Value::Bool(b))
    } else if let Ok(i) = value.extract::<i64>() {
        Ok(serde_json::Value::Number(serde_json::Number::from(i)))
    } else if let Ok(f) = value.extract::<f64>() {
        Ok(serde_json::Value::Number(serde_json::Number::from_f64(f).unwrap()))
    } else if let Ok(s) = value.extract::<String>() {
        Ok(serde_json::Value::String(s))
    } else {
        // Default to string representation
        let s = value.str()?.extract::<String>()?;
        Ok(serde_json::Value::String(s))
    }
}
