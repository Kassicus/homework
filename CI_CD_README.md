# CI/CD Pipeline Documentation

## Overview

The Contract Management Platform uses GitHub Actions for continuous integration and deployment. The pipeline ensures code quality, security, and automated testing before any code reaches production.

## Workflows

### 1. Test Suite (`test.yml`)

**Triggers:**
- Pull requests to `develop` branch
- Pushes to `develop` branch

**What it does:**
- Runs on Python versions 3.11 and 3.12 (production-ready versions)
- Performs code quality checks
- Runs security scanning
- Executes unit and integration tests
- Tests Flask app startup
- Tests database migrations
- Generates coverage reports
- Comments on PRs with results

**Code Quality Checks:**
- **isort**: Import sorting validation (runs first)
- **Black**: Code formatting validation (runs second)
- **flake8**: Linting and style checking (runs last)

**Note**: The order matters! isort runs first to organize imports, then Black formats the code, ensuring compatibility.
**Line Length**: flake8 is configured with a 120 character limit and ignores E501 (line too long) warnings.

**Security Scanning:**
- **Bandit**: Python security vulnerability scanning
- **Safety**: Dependency vulnerability checking

**Testing:**
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **App Startup**: Flask application creation test
- **Database**: Schema creation and migration tests

### 2. Build and Release (`release.yml`)

**Triggers:**
- Tags pushed to `main` branch (pattern: `v*.*.*`)

**What it does:**
- Runs full test suite on all Python versions
- Builds Python wheel package
- Creates .deb package for Ubuntu deployment
- Generates GitHub release with release notes
- Uploads package artifacts
- Sends success/failure notifications

**Package Building:**
- **Python Wheel**: Distributable Python package
- **Debian Package**: Ubuntu server installation package
- **Release Assets**: GitHub release with download links

### 3. Security Scan (`security.yml`)

**Triggers:**
- Daily at 2 AM UTC (scheduled)
- Pushes to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**What it does:**
- Scans dependencies for vulnerabilities
- Performs code security analysis
- Checks for outdated dependencies
- Creates automated issues for security concerns

## Branch Strategy

### Main Branches

- **`main`**: Production-ready code with release tags
- **`develop`**: Integration branch for ongoing development

### Feature Development

1. Create feature branch from `develop`
2. Develop and commit changes
3. Create pull request to merge into `develop`
4. Automated testing runs on PR
5. After approval and merge, delete feature branch
6. When ready for release, merge `develop` to `main` with version tag

### Release Process

1. **Development**: Work on `develop` branch
2. **Testing**: All tests must pass on `develop`
3. **Release**: Create version tag on `main` branch
4. **Automation**: GitHub Actions builds and releases package
5. **Deployment**: .deb package available for server installation

## Testing Strategy

### Test Coverage Requirements

- **Minimum Coverage**: 80%
- **Test Types**: Unit, Integration, and End-to-End
- **Python Versions**: 3.8, 3.9, 3.10, 3.11

### Test Structure

```
tests/
├── unit/           # Unit tests for individual components
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/    # Integration tests for workflows
│   ├── test_app.py
│   ├── test_auth.py
│   └── test_contracts.py
└── conftest.py     # Shared test fixtures
```

### Running Tests Locally

```bash
# Run all tests
pytest

# Run specific test types
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test function
pytest tests/unit/test_models.py::TestUserModel::test_user_creation
```

## Code Quality Standards

### Formatting

- **isort**: Import sorting and organization (runs first)
- **Black**: Code formatting (line length: 88 characters, runs second)
- **flake8**: Linting with specific rule exceptions (runs last)

**Important**: Always run isort before Black to prevent conflicts. Use the provided `format_code.py` script for consistent formatting.

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### Code Style Rules

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write comprehensive docstrings
- Keep functions under 50 lines
- Maintain cyclomatic complexity < 10

## Security Requirements

### Dependency Management

- **Regular Updates**: Automated daily vulnerability scanning
- **Security Patches**: Immediate updates for critical vulnerabilities
- **Version Pinning**: Specific versions in requirements.txt

### Code Security

- **Input Validation**: All user inputs validated
- **SQL Injection**: Parameterized queries only
- **XSS Prevention**: Output encoding and sanitization
- **Authentication**: Secure session management
- **Authorization**: Role-based access control

### Security Tools

- **Safety**: Dependency vulnerability scanning
- **Bandit**: Code security analysis
- **Automated Issues**: GitHub issues for security concerns

## Deployment Pipeline

### Package Creation

1. **Python Wheel**: `python3 -m build --wheel`
2. **Debian Package**: Custom .deb with proper structure
3. **Release Assets**: GitHub release with download links

### Installation Process

```bash
# Install .deb package
sudo dpkg -i contract-manager_1.0.0_amd64.deb
sudo apt-get install -f  # Install missing dependencies

# Verify installation
sudo systemctl status contract-manager
```

### Post-Installation

- Database initialization
- Directory structure creation
- Permission setup
- Service configuration
- Initial admin user creation

## Monitoring and Alerts

### Pipeline Status

- **Success**: All tests pass, packages built
- **Failure**: Tests fail, build errors, security issues
- **Notifications**: GitHub comments, status checks

### Coverage Reports

- **XML**: For CI/CD integration
- **HTML**: For local development
- **Terminal**: For immediate feedback

### Security Reports

- **Safety**: Dependency vulnerabilities
- **Bandit**: Code security issues
- **Automated Issues**: GitHub issues for problems

## Troubleshooting

### Common Issues

#### Test Failures

```bash
# Check test output
pytest -v

# Run specific failing test
pytest tests/unit/test_models.py::TestUserModel::test_user_creation -v

# Check coverage
pytest --cov=app --cov-report=term-missing
```

#### Build Failures

```bash
# Check Python version compatibility
python --version

# Verify dependencies
pip install -r requirements.txt

# Check for syntax errors
python -m py_compile app/

# Run linting
flake8 app/
```

#### Security Issues

```bash
# Check dependencies
safety check

# Scan code
bandit -r app/

# Update dependencies
pip3 install --upgrade -r requirements.txt
```

### Debug Mode

```bash
# Enable debug logging
export FLASK_ENV=development
export LOG_LEVEL=DEBUG

# Run with verbose output
pytest -v -s --tb=long
```

## Best Practices

### Development Workflow

1. **Always test locally** before pushing
2. **Keep tests up to date** with code changes
3. **Use meaningful commit messages** for better traceability
4. **Review security reports** regularly
5. **Maintain test coverage** above 80%

### Code Review

1. **Automated checks** must pass
2. **Test coverage** should not decrease
3. **Security scans** should show no critical issues
4. **Code quality** tools should pass
5. **Manual review** for business logic

### Release Management

1. **Semantic versioning** (v1.0.0, v1.1.0, v2.0.0)
2. **Release notes** automatically generated
3. **Package artifacts** uploaded to GitHub releases
4. **Deployment instructions** included in release notes

## Future Enhancements

### Planned Improvements

- **Performance Testing**: Load testing and benchmarks
- **Browser Testing**: Selenium-based UI testing
- **Docker Integration**: Container-based testing
- **Multi-Platform**: Windows and macOS support
- **Advanced Security**: SAST and DAST integration

### Monitoring Integration

- **Codecov**: Coverage reporting integration
- **SonarCloud**: Code quality analysis
- **Dependabot**: Automated dependency updates
- **GitHub Advanced Security**: Enhanced security scanning

---

## Quick Reference

### Commands

```bash
# Run tests
pytest

# Format code (recommended order)
python3 format_code.py

# Or format manually in correct order
isort app/
black app/

# Lint code
flake8 app/

# Security scan
safety check
bandit -r app/

# Build package
python -m build

# Create release
git tag v1.0.0
git push origin v1.0.0
```

### Workflow Triggers

- **PR to develop**: Runs test suite
- **Push to develop**: Runs test suite
- **Tag on main**: Creates release
- **Daily**: Security scanning
- **Manual**: Can be triggered manually

### Status Badges

Add these to your README.md:

```markdown
![Tests](https://github.com/username/repo/workflows/Test%20Suite/badge.svg)
![Release](https://github.com/username/repo/workflows/Build%20and%20Release/badge.svg)
![Security](https://github.com/username/repo/workflows/Security%20Scan/badge.svg)
```

---

*This documentation is automatically updated with the CI/CD pipeline configuration.*
