"""
CLI interface for LogicBridge rule engine
"""

import os
import sys
import json
import yaml
import click
from typing import Dict, Any
from pathlib import Path

from .core import RuleEngine, RuleValidationError, ExecutionError
from .audit import AuditLogger
from .validation import validate_ruleset_schema
from .llm_generator import RuleGenerator


@click.group()
@click.version_option(version="1.0.0")
def main():
    """LogicBridge - Deterministic Rule Engine with LLM Integration"""
    pass


@main.command()
@click.argument('ruleset_file', type=click.Path(exists=True))
@click.argument('payload_file', type=click.Path(exists=True))
def evaluate(ruleset_file: str, payload_file: str):
    """Evaluate a payload against a ruleset"""
    try:
        # Load and validate ruleset
        engine = RuleEngine()
        engine.load_ruleset_from_file(ruleset_file)
        
        # Load payload
        with open(payload_file, 'r') as f:
            if payload_file.endswith('.json'):
                payload = json.load(f)
            else:
                payload = yaml.safe_load(f)
        
        # Evaluate
        decision = engine.evaluate(payload)
        
        if decision:
            click.echo("✅ Rule matched!")
            click.echo(f"Rule ID: {decision.rule_id}")
            click.echo(f"Outcome: {json.dumps(decision.outcome, indent=2)}")
            click.echo(f"Elapsed: {decision.elapsed_us}μs")
        else:
            click.echo("❌ No rules matched")
            
    except (RuleValidationError, ExecutionError) as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('ruleset_file', type=click.Path(exists=True))
@click.argument('test_dir', type=click.Path(exists=True))
def test(ruleset_file: str, test_dir: str):
    """Run golden-set tests against a ruleset"""
    try:
        # Load ruleset
        engine = RuleEngine()
        engine.load_ruleset_from_file(ruleset_file)
        
        # Find test files
        test_files = list(Path(test_dir).glob('*.yml')) + list(Path(test_dir).glob('*.yaml'))
        
        if not test_files:
            click.echo("❌ No test files found")
            sys.exit(1)
        
        total_tests = 0
        passed_tests = 0
        
        click.echo(f"Running tests from {len(test_files)} file(s)...")
        click.echo()
        
        for test_file in test_files:
            with open(test_file, 'r') as f:
                test_cases = yaml.safe_load(f)
            
            if not isinstance(test_cases, list):
                test_cases = [test_cases]
            
            for i, test_case in enumerate(test_cases):
                total_tests += 1
                test_name = test_case.get('name', f"{test_file.name}[{i}]")
                
                try:
                    # Run evaluation
                    decision = engine.evaluate(test_case['input'])
                    
                    # Check expected output
                    expected = test_case.get('expected_output')
                    if expected:
                        if decision and decision.outcome == expected:
                            click.echo(f"✅ {test_name}")
                            passed_tests += 1
                        elif not decision and expected is None:
                            click.echo(f"✅ {test_name}")
                            passed_tests += 1
                        else:
                            click.echo(f"❌ {test_name} - Expected {expected}, got {decision.outcome if decision else None}")
                    else:
                        # Just check if rule matched
                        expected_rule = test_case.get('expected_rule_id')
                        if expected_rule:
                            if decision and decision.rule_id == expected_rule:
                                click.echo(f"✅ {test_name}")
                                passed_tests += 1
                            else:
                                click.echo(f"❌ {test_name} - Expected rule {expected_rule}, got {decision.rule_id if decision else None}")
                        else:
                            click.echo(f"⚠️  {test_name} - No assertions defined")
                            passed_tests += 1
                            
                except Exception as e:
                    click.echo(f"❌ {test_name} - Error: {e}")
        
        click.echo()
        click.echo(f"Results: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests < total_tests:
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--stories', type=click.Path(exists=True), help='Excel file with user stories')
@click.option('--provider', default='openai', help='LLM provider')
@click.option('--model', default='gpt-4o', help='LLM model')
@click.option('--output', '-o', default='generated_rules.yml', help='Output file')
def gen(stories: str, provider: str, model: str, output: str):
    """Generate rules from user stories using LLM"""
    try:
        generator = RuleGenerator(provider=provider, model=model)
        
        if stories:
            # Generate from Excel file
            rules = generator.generate_from_excel(stories)
        else:
            click.echo("❌ No input source specified. Use --stories option.")
            sys.exit(1)
        
        # Save generated rules
        with open(output, 'w') as f:
            yaml.dump(rules, f, default_flow_style=False, sort_keys=False)
        
        click.echo(f"✅ Generated {len(rules.get('rules', []))} rules -> {output}")
        
        # Validate generated rules
        try:
            validate_ruleset_schema(yaml.dump(rules), "yaml")
            click.echo("✅ Generated rules passed validation")
        except Exception as e:
            click.echo(f"⚠️  Generated rules have validation issues: {e}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--since', default='30d', help='Show changes since (e.g., 7d, 30d)')
@click.option('--limit', default=50, help='Maximum number of entries')
def log(since: str, limit: int):
    """Show audit log of rule changes"""
    try:
        audit_logger = AuditLogger()
        entries = audit_logger.get_log_entries(limit=limit, since=since)
        
        if not entries:
            click.echo("No audit log entries found")
            return
        
        click.echo(f"Recent rule changes ({len(entries)} entries):")
        click.echo()
        
        for entry in entries:
            click.echo(f"📅 {entry['timestamp']} | {entry['author']}")
            click.echo(f"   SHA: {entry['rule_sha'][:12]}...")
            if entry.get('llm_model'):
                click.echo(f"   LLM: {entry['llm_model']}")
            click.echo()
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('rule_sha1')
@click.argument('rule_sha2')
def diff(rule_sha1: str, rule_sha2: str):
    """Show differences between two rule versions"""
    try:
        audit_logger = AuditLogger()
        diff_result = audit_logger.get_rule_diff(rule_sha1, rule_sha2)
        
        if diff_result:
            click.echo(f"Differences between {rule_sha1[:12]}... and {rule_sha2[:12]}...")
            click.echo(diff_result)
        else:
            click.echo("No differences found or rules not in audit log")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('ruleset_file', type=click.Path(exists=True))
def validate(ruleset_file: str):
    """Validate a ruleset file"""
    try:
        with open(ruleset_file, 'r') as f:
            content = f.read()
        
        format = "yaml" if ruleset_file.endswith(('.yml', '.yaml')) else "json"
        validate_ruleset_schema(content, format)
        
        # Also validate with engine
        engine = RuleEngine()
        engine.load_ruleset_from_file(ruleset_file)
        
        click.echo("✅ Ruleset validation passed")
        click.echo(f"Rule SHA: {engine.get_ruleset_sha()}")
        
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
def serve(host: str, port: int):
    """Start the web API server"""
    try:
        import uvicorn
        from .api import create_app
        
        app = create_app()
        click.echo(f"🚀 Starting LogicBridge API server on http://{host}:{port}")
        uvicorn.run(app, host=host, port=port)
        
    except ImportError:
        click.echo("❌ uvicorn not installed. Install with: pip install uvicorn", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
