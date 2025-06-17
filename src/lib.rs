use pyo3::prelude::*;

mod engine;
mod dsl;
mod python_bindings;

pub use engine::*;
pub use dsl::*;

/// Python module for LogicBridge rule engine
#[pymodule]
fn logicbridge_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<python_bindings::PyRuleEngine>()?;
    m.add_class::<python_bindings::PyDecision>()?;
    m.add_class::<python_bindings::PyRuleSet>()?;
    Ok(())
}
