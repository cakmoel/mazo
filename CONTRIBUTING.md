# Contributing to Mazo

Thank you for your interest in contributing to Mazo! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- **Python 3.7+** development environment
- **Git** for version control
- **GitHub account** for pull requests
- **Basic knowledge** of load testing and web applications

### Development Setup

1. **Fork the repository**:
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/mazo.git
   cd mazo
   ```

2. **Set up development environment**:
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r loadrequirements.txt
   ```

3. **Verify setup**:
   ```bash
   # Run tests to ensure everything works
   ./run_tests.sh
   ```

## Contribution Guidelines

### Code Style

Mazo uses automated code formatting and linting:

```bash
# Format code
black locustfile.py
isort locustfile.py

# Check linting
flake8 locustfile.py
mypy locustfile.py --ignore-missing-imports
```

- **Line length**: 120 characters maximum
- **Import order**: Standard library, third-party, local imports
- **Documentation**: Docstrings for public functions/classes
- **Type hints**: Optional but encouraged for new code

### Testing

All contributions must include tests:

```bash
# Run all tests
./run_tests.sh

# Run specific test types
pytest tests/python/ -v
bats tests/bash/
```

#### Test Coverage
- **New features**: Add unit tests
- **Bug fixes**: Add regression tests
- **Maintain coverage**: Aim for 80%+ coverage
- **Integration tests**: For major functionality

### Commit Guidelines

#### Commit Messages
Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer(s)]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:
- `feat(auth): add OAuth2 authentication support`
- `fix(routing): handle malformed route definitions`
- `docs(readme): update installation instructions`
- `test(api): add integration tests for endpoints`

#### Branch Strategy
- **main**: Stable, production-ready code
- **develop**: Integration branch for features
- **feature/NAME**: Individual feature branches
- **hotfix/NAME**: Critical bug fixes

### Pull Request Process

1. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** following the guidelines above

3. **Test thoroughly**:
   ```bash
   # Run all tests
   ./run_tests.sh
   ```

4. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**:
   - Use descriptive title
   - Fill out PR template
   - Link relevant issues
   - Request review from maintainers

## Development Workflow

### Types of Contributions

#### 🐛 Bug Reports
- Use issue templates for bug reports
- Include reproduction steps
- Provide environment details
- Attach logs/error messages if available

#### ✨ Features
- Open issue for discussion first
- Design and plan implementation
- Consider backwards compatibility
- Update documentation

#### 📚 Documentation
- Fix typos and grammar
- Improve clarity and examples
- Add missing information
- Update README/API docs

#### 🧪 Testing
- Increase test coverage
- Add integration tests
- Fix flaky tests
- Improve test infrastructure

#### 🔧 Tools & Infrastructure
- Improve development setup
- Add automation scripts
- Enhance CI/CD pipelines
- Documentation improvements

### Code Review Process

#### What Reviewers Look For
- **Functionality**: Does the code work as intended?
- **Testing**: Are tests comprehensive and passing?
- **Style**: Does it follow project conventions?
- **Documentation**: Is the code well documented?
- **Security**: Are there any security concerns?
- **Performance**: Will this impact performance?

#### Review Guidelines
- **Constructive**: Focus on code, not the author
- **Specific**: Provide clear, actionable feedback
- **Polite**: Professional and respectful communication
- **Thorough**: Check all aspects of the change

## Project Structure

```
mazo/
├── locustfile.py          # Main load testing logic
├── locust.sh              # Setup and execution script
├── loadrequirements.txt   # Python dependencies
├── routes.json           # Application route definitions
├── tests/                # Test suite
│   ├── python/           # Python tests
│   └── bash/             # Shell script tests
├── .flake8               # Linting configuration
├── pyproject.toml         # Code formatting config
├── pytest.ini            # Test configuration
├── run_tests.sh          # Local test runner
├── README.md              # Project documentation
├── CONTRIBUTING.md         # This file
├── LICENSE.md              # License information
├── SECURITY.md            # Security policy
├── LINTING.md            # Linting guide
└── TESTING.md            # Testing guide
```

## Development Best Practices

### Code Quality
- **Small commits**: Atomic, focused changes
- **Descriptive names**: Clear, meaningful identifiers
- **Comments**: Explain "why" not "what"
- **Error handling**: Graceful degradation
- **Resource management**: Proper cleanup and disposal

### Performance
- **Efficient algorithms**: Consider time/space complexity
- **Resource usage**: Monitor memory and CPU
- **Caching**: Implement where appropriate
- **Async operations**: Use for I/O-bound tasks

### Security
- **Input validation**: Sanitize all inputs
- **Authentication**: Secure credential handling
- **Error messages**: Don't expose sensitive info
- **Dependencies**: Keep updated, review regularly

### Testing
- **Test isolation**: Independent, repeatable tests
- **Edge cases**: Handle boundary conditions
- **Mocking**: Isolate external dependencies
- **Documentation**: Document test scenarios

## Release Process

### Version Management
- **Semantic versioning**: MAJOR.MINOR.PATCH
- **Release notes**: Document all changes
- **Tagging**: Git tags for releases
- **Changelog**: Maintain change history

### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Version numbers updated
- [ ] Security review completed
- [ ] Performance testing done
- [ ] Release notes prepared

## Community

### Communication Channels
- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: General questions, ideas
- **Pull Requests**: Code contributions, reviews
- **Email**: security@example.com (security issues only)

### Code of Conduct

Please review [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for our community guidelines.

### Getting Help

- **Documentation**: Check [README.md](README.md) and [TESTING.md](TESTING.md)
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Maintainers**: Tag maintainers in issues for direct help

## Recognition

### Contributor Credits
- **AUTHORS.md**: List all contributors
- **Release notes**: Credit significant contributions
- **README**: Acknowledge key contributors
- **GitHub**: Contributor statistics and graphs

### Ways to Contribute
- **Code**: New features, bug fixes, improvements
- **Documentation**: README, guides, API docs
- **Testing**: Bug reports, test cases, test infrastructure
- **Design**: UI/UX improvements, graphics, icons
- **Community**: Answer questions, review PRs, promote project

## License

By contributing to Mazo, you agree that your contributions will be licensed under the MIT License, as specified in [LICENSE.md](LICENSE.md).

---

Thank you for contributing to Mazo! Your contributions help make this project better for everyone. 🚀