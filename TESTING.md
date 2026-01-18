# Testing Guide

This document explains the testing framework implemented for the Mazo load testing suite.

## Overview

Mazo includes a comprehensive testing suite covering:

- **Python Unit Tests** - Testing core Locust functionality
- **Shell Script Tests** - Testing the locust.sh launcher script
- **Static Analysis** - Code quality and security scanning
- **Integration Tests** - End-to-end functionality validation

## Test Structure

```
mazo/
├── tests/                    # Python tests
│   ├── conftest.py          # Test fixtures and configuration
│   ├── test_route_loader.py # RouteLoader class tests
│   ├── test_user_classes.py # User class and authentication tests
│   └── test_integration.py  # Integration tests with real routes
├── test/bats/               # BATS shell tests
│   ├── locust_basic.bats    # Basic script functionality tests
│   └── shellcheck.bats      # Shell script linting tests
├── .github/workflows/       # CI/CD configuration
│   └── ci.yml              # GitHub Actions pipeline
├── pytest.ini              # Pytest configuration
├── loadrequirements.txt     # Dependencies (including test deps)
└── run_tests.sh            # Local test runner
```

## Running Tests Locally

### Quick Test Run

Run all tests with the test runner:

```bash
./run_tests.sh
```

### Individual Test Categories

#### Python Unit Tests

```bash
# Install test dependencies
pip install -r loadrequirements.txt

# Run all Python tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=locustfile --cov-report=html

# Run specific test file
pytest tests/test_route_loader.py -v

# Run with markers
pytest tests/ -m unit -v
pytest tests/ -m integration -v
```

#### Shell Script Tests

```bash
# Install BATS (if not already installed)
sudo apt-get install bats

# Run all shell tests
bats test/bats/

# Run specific test file
bats test/bats/locust_basic.bats
```

#### Static Analysis

```bash
# Shell script linting
shellcheck locust.sh

# Python code formatting check
black --check locustfile.py

# Import sorting check
isort --check-only locustfile.py

# Python linting
flake8 locustfile.py
```

## Test Coverage

### Python Tests Coverage

- **RouteLoader Class** (95%+ coverage):
  - Route loading and parsing
  - New and backward-compatible formats
  - Error handling and validation
  - URL generation and selection

- **User Classes** (90%+ coverage):
  - BaseUser functionality
  - Authentication flows
  - CSRF token extraction
  - Task methods for ReaderUser and AdminUser

- **Integration Tests**:
  - Real routes.json structure handling
  - Public vs protected route classification
  - Multi-URL route handling
  - API route validation

### Shell Tests Coverage

- **Script Functionality**:
  - Command-line argument parsing
  - Help system and defaults
  - Environment setup and validation
  - Configuration file handling

- **Static Analysis**:
  - ShellCheck compliance
  - Bash best practices
  - Security considerations
  - Error handling patterns

## CI/CD Pipeline

The GitHub Actions workflow runs on:

- **Push** to `main` or `develop` branches
- **Pull Requests** to `main` branch

### Workflow Stages

1. **Python Tests** - Multi-version Python testing (3.8-3.11)
2. **Shell Tests** - BATS and ShellCheck validation
3. **Security Scan** - Bandit and Safety scanning
4. **Code Quality** - Black, isort, Flake8 checks
5. **Integration Test** - End-to-end functionality
6. **Build Status** - Overall pipeline status

### Coverage Reporting

Test coverage is automatically uploaded to Codecov for tracking and visualization.

## Writing New Tests

### Python Tests

Add test files to the `tests/` directory following the naming convention `test_*.py`:

```python
#!/usr/bin/env python3
"""Test example for new functionality"""

import pytest
from unittest.mock import Mock, patch

class TestNewFeature:
    def test_basic_functionality(self):
        """Test basic feature behavior"""
        # Your test code here
        assert True
    
    @pytest.fixture
    def mock_dependency(self):
        """Create a mock dependency"""
        return Mock()
```

### Shell Tests

Add BATS tests to `test/bats/`:

```bash
#!/usr/bin/env bats

@test "new feature works correctly" {
    run ./locust.sh --new-feature
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Expected output" ]]
}
```

## Test Data

### Sample Routes Structure

Tests use a simplified version of your actual routes.json:

```json
{
  "home": {
    "urls": ["/"],
    "methods": ["GET"],
    "controller": "PostController@home"
  },
  "single": {
    "urls": ["/post/8/cicero", "/post/6/kafka"],
    "methods": ["GET"],
    "controller": "PostController@show"
  }
}
```

## Debugging Tests

### Python Tests

```bash
# Run with verbose output
pytest tests/ -v -s

# Run specific test with debugging
pytest tests/test_route_loader.py::TestRouteLoader::test_load_routes_success_new_format -v -s

# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l
```

### Shell Tests

```bash
# Run with verbose output
bats -t test/bats/

# Run specific test
bats -t test/bats/locust_basic.bats

# Show test output
bats -p test/bats/
```

## Performance Considerations

- Tests are optimized for speed with mocked dependencies
- Integration tests use minimal sample data
- CI/CD pipeline caches pip dependencies
- Parallel execution is used where possible

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root
2. **Missing Dependencies**: Run `pip install -r loadrequirements.txt`
3. **Permission Issues**: Ensure `locust.sh` is executable (`chmod +x locust.sh`)
4. **BATS Not Found**: Install with `sudo apt-get install bats`

### Test Failures

Check the test output for specific error messages. Most tests include detailed assertions that help identify the root cause.

## Contributing

When adding new features:

1. Write tests for the new functionality
2. Ensure existing tests still pass
3. Aim for 80%+ code coverage
4. Follow the established test patterns
5. Update this documentation if needed

Run the full test suite before submitting:

```bash
./run_tests.sh
```

This ensures all quality checks pass and your contribution is ready for merge.