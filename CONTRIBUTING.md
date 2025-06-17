# Contributing to Newton.RS

Thank you for your interest in contributing to Newton.RS! This document provides guidelines for contributing to the project.


## Getting Started

### Prerequisites

- Python 3.11 or higher
- Rust toolchain (for core engine development)
- Git


# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/

# Start development server
python main.py
```

## Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use type hints for all function signatures
- Maintain comprehensive docstrings
- Keep functions focused and testable

### Testing

- Write unit tests for all new functionality
- Include integration tests for API endpoints
- Test business rule scenarios thoroughly
- Maintain >90% code coverage

### Documentation

- Update API documentation for new endpoints
- Include examples in docstrings
- Update system specification for architectural changes
- Provide clear commit messages

## Contributing Process

### 1. Create an Issue

Before making changes, create an issue to discuss:
- Bug reports with reproduction steps
- Feature requests with use cases
- Documentation improvements
- Performance optimizations

### 2. Fork and Branch

```bash
# Fork the repository on GitHub

# Create feature branch
git checkout -b feature/your-feature-name
```

### 3. Development

- Make focused commits with clear messages
- Include tests for new functionality
- Update documentation as needed
- Follow existing code patterns

### 4. Testing

```bash
# Run full test suite
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_api.py
python -m pytest tests/test_business_rules.py

# Check code coverage
python -m pytest --cov=logicbridge tests/
```

### 5. Submit Pull Request

- Push changes to your fork
- Create pull request with descriptive title
- Include issue reference in description
- Add reviewers if known

## Code Review Process

### Review Criteria

- Code quality and style compliance
- Test coverage and reliability
- Documentation completeness
- Performance considerations
- Security implications

### Review Timeline

- Initial review within 48 hours
- Feedback addressing within 1 week
- Final approval and merge within 2 weeks

## Areas for Contribution

### Core Engine

- Rule evaluation performance optimizations
- New condition types and operators
- Memory usage improvements
- Error handling enhancements

### API Development

- New endpoint functionality
- Request/response optimization
- Authentication and authorization
- Rate limiting and throttling

### LLM Integration

- Additional provider support
- Rule generation improvements
- Natural language processing
- Prompt engineering optimization

### Documentation

- API documentation updates
- Tutorial development
- Example scenarios
- Architecture diagrams

### Testing

- Unit test expansion
- Integration test scenarios
- Performance benchmarking
- Security testing

## Bug Reports

### Issue Template

When reporting bugs, include:

```markdown
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- Newton.RS version:
- Python version:
- Operating system:
- Additional dependencies:

## Additional Context
Logs, screenshots, or other relevant information
```

## Feature Requests

### Request Template

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Specific business scenarios this addresses

## Proposed Implementation
High-level approach or design ideas

## Alternatives Considered
Other solutions evaluated

## Additional Context
Supporting information or examples
```

## Security


### Security Guidelines

- Never commit credentials or API keys
- Use environment variables for configuration
- Validate all input data thoroughly
- Follow secure coding practices

## Release Process

### Version Numbering

Newton.RS follows semantic versioning (SemVer):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Schedule

- Patch releases: As needed for critical bugs
- Minor releases: Monthly feature updates
- Major releases: Quarterly with breaking changes

## Community

### Communication Channels

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and general discussion


### Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please:

- Be respectful and constructive in all interactions
- Focus on technical merit in code reviews
- Help newcomers get started
- Follow project guidelines and standards

## Recognition

Contributors are recognized through:
- GitHub contributor statistics
- Release notes acknowledgments
- Project documentation credits
- Community highlights

## Getting Help

If you need help contributing:
- Check existing documentation
- Search closed issues for similar problems
- Ask questions in GitHub Discussions
- Contact maintainers via email

Thank you for contributing to Newton.RS!
