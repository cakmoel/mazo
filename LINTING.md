# Linting Guide

This document explains the Python linting and code quality tools implemented for the Mazo project.

## Overview

Mazo uses a comprehensive linting stack to maintain code quality and consistency:

- **Black** - Code formatting and style
- **isort** - Import statement sorting
- **flake8** - Code linting and error checking
- **MyPy** - Static type checking

## Configuration Files

### pyproject.toml

Contains Black and isort configuration:

```toml
[tool.black]
line-length = 120
target-version = ['py37', 'py38', 'py39', 'py310', 'py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 120
multi_line_output = 3
include_trailing_comma = true
```

### .flake8

Contains flake8 configuration:

```ini
[flake8]
max-line-length = 120
extend-ignore = E203, W503, E501
exclude = venv, __pycache__, .pytest_cache, htmlcov
max-complexity = 10
```

### .mypy.ini

Contains MyPy type checking configuration:

```ini
[mypy]
python_version = 3.7
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False
```

## Usage

### Installation

Linting tools are included in `loadrequirements.txt`:

```bash
pip install -r loadrequirements.txt
```

### Individual Tools

#### Black - Code Formatting

```bash
# Check formatting
black --check --diff locustfile.py

# Apply formatting
black locustfile.py

# Format all Python files
black *.py tests/python/*.py
```

#### isort - Import Sorting

```bash
# Check import order
isort --check-only --diff locustfile.py

# Apply import sorting
isort locustfile.py

# Sort all imports
isort *.py tests/python/*.py
```

#### flake8 - Linting

```bash
# Lint main file
flake8 locustfile.py

# Lint all Python files
flake8 *.py tests/python/

# Lint with specific config
flake8 --config=.flake8 locustfile.py
```

#### MyPy - Type Checking

```bash
# Type check main file
mypy locustfile.py

# Type check with ignore missing imports
mypy locustfile.py --ignore-missing-imports

# Type check all files
mypy *.py tests/python/
```

### Integrated Testing

The `run_tests.sh` script includes all linting checks:

```bash
./run_tests.sh
```

This runs:
1. Black formatting check
2. isort import sorting check  
3. flake8 linting
4. MyPy type checking

## Code Style Standards

### Formatting

- **Line Length**: 120 characters maximum
- **Indentation**: 4 spaces (Black enforced)
- **String Quotes**: Double quotes preferred
- **Import Style**: Black profile compatible

### Import Order

1. Standard library imports
2. Third-party imports
3. Local application imports
4. Relative imports

### Linting Rules

Key flake8 rules enforced:
- **E203**: Whitespace before ':' (ignored for Black compatibility)
- **W503**: Line break before binary operator (ignored for Black compatibility)
- **E501**: Line too long (handled by Black)
- **C901**: Too complex (max complexity 10)
- **F401**: Unused imports
- **F841**: Unused variables

## Pre-commit Integration

For development, consider adding pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
```

## Troubleshooting

### Common Issues

#### Black conflicts with flake8
- **Solution**: Ignore E203 and W503 in flake8 config
- **Reason**: Black formatting may conflict with these rules

#### Import sorting conflicts
- **Solution**: Use `profile = "black"` in isort config
- **Reason**: Ensures compatibility with Black

#### MyPy errors with external libraries
- **Solution**: Use `--ignore-missing-imports` flag
- **Reason**: External libraries may not have type stubs

#### Complex function warnings
- **Solution**: Refactor complex functions (>10 complexity)
- **Reason**: Improves maintainability and readability

### IDE Integration

#### VS Code
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

#### PyCharm
- Enable Black integration
- Configure flake8 as external tool
- Set up MyPy type checking

## Automated Enforcement

The CI/CD pipeline (when implemented) will:
1. Run Black formatting check
2. Verify isort import order
3. Execute flake8 linting
4. Perform MyPy type checking

Any failure in these checks will block the pipeline, ensuring code quality standards are maintained.

## Best Practices

1. **Format before committing**: Run `black` and `isort` on changed files
2. **Check linting locally**: Use `./run_tests.sh` to verify
3. **Address warnings**: Fix flake8 warnings, don't ignore them
4. **Type hints**: Add type annotations where beneficial
5. **Complexity**: Keep functions simple and focused
6. **Consistency**: Use the same style across all files

## Performance Considerations

- **Black**: Fast formatting, minimal overhead
- **isort**: Quick import sorting
- **flake8**: Moderate speed, can be slowed by complex files
- **MyPy**: Slowest due to type inference

For large codebases, consider:
- Incremental linting on changed files only
- Parallel execution where possible
- Caching type information