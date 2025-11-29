# Testing Guide

This document describes the testing infrastructure and improvements made to the Kasparro Agentic FB Analyst system.

## Table of Contents

- [Overview](#overview)
- [Test Coverage](#test-coverage)
- [Running Tests](#running-tests)
- [CI/CD Pipeline](#cicd-pipeline)
- [Code Quality Tools](#code-quality-tools)
- [Schema Versioning](#schema-versioning)

## Overview

The system now includes comprehensive testing infrastructure with:
- ✅ Unit tests for all agents (70%+ coverage target)
- ✅ Integration tests for orchestrator workflows
- ✅ Enhanced logging with timing and error tracking
- ✅ Retry logic with exponential backoff
- ✅ Fallback behaviors for agent failures
- ✅ Schema versioning and validation
- ✅ CI/CD pipeline with GitHub Actions
- ✅ Pre-commit hooks for code quality

## Test Coverage

### Unit Tests

#### 1. Data Agent Tests (`tests/test_data_agent.py`)
- ✅ Agent initialization
- ✅ Data loading and caching
- ✅ Data summary generation
- ✅ ROAS analysis over time
- ✅ CTR analysis
- ✅ Low-performing campaign identification
- ✅ Top performer extraction
- ✅ Missing value handling
- ✅ Date parsing

#### 2. Planner Agent Tests (`tests/test_planner.py`)
- ✅ Agent initialization
- ✅ Query decomposition
- ✅ Subtask structure validation
- ✅ Task count calculation
- ✅ Query preservation
- ✅ Complex query handling
- ✅ Empty query handling

#### 3. Insight Agent Tests (`tests/test_insight_agent.py`)
- ✅ Agent initialization
- ✅ Hypothesis generation
- ✅ Hypothesis structure validation
- ✅ Confidence score validation
- ✅ Confidence bounds checking
- ✅ Missing confidence default values
- ✅ Multiple hypothesis generation
- ✅ Hypothesis ID uniqueness

#### 4. Evaluator Tests (`tests/test_evaluator.py`)
- ✅ Agent initialization
- ✅ Hypothesis evaluation
- ✅ Confidence threshold filtering
- ✅ Validation status assignment
- ✅ Evidence categorization

#### 5. Creative Generator Tests (`tests/test_creative_generator.py`)
- ✅ Agent initialization
- ✅ Recommendation generation
- ✅ Recommendation structure validation
- ✅ Creative variation generation
- ✅ DataFrame formatting
- ✅ Empty data handling
- ✅ Insights formatting
- ✅ Timestamp generation

### Integration Tests

#### Orchestrator Tests (`tests/test_orchestrator.py`)
- ✅ End-to-end workflow execution
- ✅ State management across agents
- ✅ Agent execution order verification
- ✅ Error handling and recovery
- ✅ Result structure validation

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_data_agent.py -v

# Run with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing

# Run tests in parallel (faster)
pytest tests/ -v -n auto
```

### Coverage Targets

The project aims for **70-80% code coverage**:

```bash
# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Test Markers

Tests are categorized with markers:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run only API-related tests
pytest -m api
```

## CI/CD Pipeline

### GitHub Actions Workflow

The CI pipeline (`.github/workflows/ci.yml`) runs on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Pipeline Jobs:**

1. **Test Job**
   - Runs on Python 3.10 and 3.11
   - Installs dependencies
   - Runs linting (flake8)
   - Checks code formatting (black)
   - Runs type checking (mypy)
   - Executes unit tests with coverage
   - Uploads coverage to Codecov

2. **Lint Job**
   - Runs flake8 for code quality
   - Checks formatting with black
   - Runs mypy for type safety

3. **Security Job**
   - Checks dependencies for vulnerabilities (safety)
   - Runs security linter (bandit)
   - Uploads security reports

### Manual CI Commands

Run the same checks locally:

```bash
# Linting
make lint

# Formatting check
make format-check

# Type checking
make type-check

# All checks
make check

# Run tests
make test

# Full CI simulation
make ci
```

## Code Quality Tools

### Pre-commit Hooks

Install pre-commit hooks to automatically check code before commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

**Enabled Hooks:**
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON validation
- Large file detection
- Merge conflict detection
- Private key detection
- Code formatting (black)
- Import sorting (isort)
- Linting (flake8)
- Security checks (bandit)
- Docstring coverage (interrogate)

### Code Formatting

```bash
# Format code with black
black src tests

# Check formatting without changes
black --check src tests

# Sort imports
isort src tests
```

### Linting

```bash
# Run flake8
flake8 src tests

# Run with specific rules
flake8 src tests --max-line-length=127
```

### Type Checking

```bash
# Run mypy
mypy src --ignore-missing-imports
```

### Security Scanning

```bash
# Check dependencies for vulnerabilities
safety check

# Run bandit security linter
bandit -r src
```

## Enhanced Logging

### Features

The logging system now includes:

- **Automatic timing**: Logs duration of agent operations
- **Error tracking**: Captures full stack traces for errors
- **Structured metadata**: Session IDs, agent names, event types
- **Color-coded console output**: Easy visual parsing
- **Summary statistics**: Get performance metrics per session

### Usage

```python
from utils.logger import Logger

# Initialize logger
logger = Logger(config)

# Log events
logger.log('agent_name', 'start', {})
logger.log('agent_name', 'complete', {'result_count': 5})

# Log metrics
logger.log_metric('data_agent', 'processing_time', 145.2, unit='ms')

# Log errors
try:
    risky_operation()
except Exception as e:
    logger.log_error('agent_name', e, {'context': 'additional info'})

# Log warnings
logger.log_warning('agent_name', 'Low confidence', {'confidence': 0.55})

# Get session summary
stats = logger.get_summary_stats()
print(f"Total events: {stats['total_events']}")
print(f"Total duration: {stats['total_duration_ms']}ms")
```

### Log Output Format

```json
{
  "timestamp": "2025-11-28T10:30:45.123456",
  "session_id": "20251128_103045",
  "agent": "data_agent",
  "event": "complete",
  "level": "INFO",
  "duration_ms": 145.23,
  "data": {
    "findings": 5,
    "hypotheses": 3
  },
  "metadata": {
    "agent_name": "data_agent",
    "event_type": "complete",
    "has_error": false,
    "data_keys": ["findings", "hypotheses"]
  }
}
```

## Retry Logic & Error Handling

### Configuration

Add to `config/config.yaml`:

```yaml
llm:
  model: "gpt-4o"
  temperature: 0.3
  max_tokens: 2500
  # Retry configuration
  max_retries: 3
  initial_retry_delay: 1.0  # seconds
  max_retry_delay: 60.0     # seconds
  backoff_factor: 2.0       # exponential multiplier
```

### Retry Behavior

The system automatically retries on:
- Rate limit errors
- API connection errors
- API timeout errors
- Internal server errors
- Service unavailable errors

**Exponential Backoff:**
- Attempt 1: Wait 1.0s
- Attempt 2: Wait 2.0s
- Attempt 3: Wait 4.0s (up to max_retry_delay)

### Fallback Behaviors

Agents now implement graceful degradation:

1. **Data Agent**: Returns partial results if some analyses fail
2. **Insight Agent**: Continues with available hypotheses
3. **Evaluator**: Marks hypotheses as "insufficient_data" if validation fails
4. **Creative Generator**: Generates recommendations for available campaigns

## Schema Versioning

### Schema Validator

Validates agent outputs against defined schemas:

```python
from utils.schema import SchemaValidator

# Validate planner output
is_valid, issues = SchemaValidator.validate_planner_output(data)
if not is_valid:
    print("Validation issues:", issues)

# Add schema version to output
data = SchemaValidator.add_schema_version(data, 'planner')

# Check for schema drift
warnings = check_schema_drift(old_data, new_data)
```

### Schema Definitions

Schemas are versioned and include:
- Required fields
- Optional fields
- Nested structure definitions
- Field type constraints

**Current Schema Version:** 1.0.0

### Drift Detection

Automatically detect schema changes:

```python
from utils.schema import check_schema_drift

old_output = load_historical_output()
new_output = current_agent_output()

warnings = check_schema_drift(old_output, new_output)
for warning in warnings:
    print(f"⚠️  {warning}")
```

Common drift scenarios:
- Version changes
- Added fields
- Removed fields
- Nested structure changes

### Save Schema Documentation

```python
from utils.schema import save_schema_definitions

# Save all schema definitions
save_schema_definitions('docs/schemas.json')
```

## Performance Benchmarks

Expected performance after improvements:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Test Coverage | ~20% | 70-80% | +250% |
| CI/CD Pipeline | None | Full | ✅ |
| Error Recovery | None | Automatic | ✅ |
| Logging Depth | Basic | Comprehensive | ✅ |
| Schema Validation | None | Versioned | ✅ |

## Continuous Improvement

### Coverage Goals

- [ ] Reach 80%+ overall coverage
- [ ] 100% coverage for critical paths
- [ ] Add performance benchmarks
- [ ] Add load testing

### Future Enhancements

- [ ] Mutation testing with mutmut
- [ ] Property-based testing with hypothesis
- [ ] Contract testing for APIs
- [ ] Visual regression testing for reports
- [ ] Load testing with locust

## Troubleshooting

### Common Issues

**Issue: Tests fail with import errors**
```bash
# Solution: Add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
pytest tests/
```

**Issue: Coverage too low**
```bash
# Solution: Check which files are missing tests
pytest --cov=src --cov-report=term-missing
```

**Issue: Pre-commit hooks fail**
```bash
# Solution: Run hooks manually to see errors
pre-commit run --all-files --verbose
```

**Issue: CI pipeline fails on GitHub**
```bash
# Solution: Run CI checks locally first
make ci
```

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure tests pass: `pytest tests/ -v`
3. Check coverage: `pytest --cov=src --cov-report=term-missing`
4. Run pre-commit hooks: `pre-commit run --all-files`
5. Verify CI passes: `make ci`
6. Update schema if needed: Update `src/utils/schema.py`
7. Document changes in this file

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Pre-commit Framework](https://pre-commit.com/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Black Code Formatter](https://black.readthedocs.io/)
- [Flake8 Linter](https://flake8.pycqa.org/)
