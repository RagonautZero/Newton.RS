# Newton.RS - Deterministic Rule Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

A high-performance, deterministic rule engine with LLM integration for auditable business rule validation and generation.


## 🚀 Features

- **Deterministic Rule Engine**: Rust core with <50μs per rule performance
- **YAML/JSON DSL**: Human-readable rule definitions with clean Git diffs
- **Python API**: FastAPI-based REST endpoints with type safety
- **LLM Integration**: OpenAI-powered rule generation from user stories
- **Audit Trail**: Complete SHA-based versioning and change tracking
- **CLI Tools**: Comprehensive command-line interface for rule management
- **Web Interface**: User-friendly web UI for testing and visualization
- **Schema Validation**: JSON Schema enforcement with safety checks
- **Golden-Set Testing**: Automated test harness for rule validation

## 📋 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/RagonautZero/Newton.RS.git
cd Newton.RS

# Install Python dependencies
pip install -e .

# Build Rust core (requires Rust toolchain)
maturin develop --release
