# Test Suite for Langflow CLI

This directory contains the test suite for the Langflow CLI tool. Tests are organized by command group, with each command group having its own test file.

## Setup

### Install Test Dependencies

Before running tests, install the development dependencies:

```bash
# Using uv
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

This will install:
- `pytest` - Test framework
- `pytest-mock` - Mocking utilities
- `pytest-cov` - Coverage reporting
- `build` - Package building tools
- `twine` - Package publishing tools

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Tests for a Specific Command Group

```bash
# Run environment command tests
pytest tests/test_env.py

# Run with verbose output
pytest -v tests/test_env.py
```

### Run a Specific Test Class

```bash
pytest tests/test_env.py::TestEnvRegister
```

### Run a Specific Test

```bash
pytest tests/test_env.py::TestEnvRegister::test_register_new_profile
```

### Run Tests with Coverage

```bash
# Generate coverage report
pytest --cov=langflow_cli --cov-report=html

# View coverage in terminal
pytest --cov=langflow_cli --cov-report=term
```

The HTML coverage report will be generated in `htmlcov/index.html`.

### Run Tests in Watch Mode

```bash
# Install pytest-watch first
pip install pytest-watch

# Run tests in watch mode
ptw
```

## Test Structure

Tests are organized by command group, with each group having its own test file:

- `test_env.py` - Environment/profile management commands
- (More test files will be added for other command groups)

Each test file contains test classes that group related tests together.

## Test Coverage

### Environment Commands (`test_env.py`)

Tests for the `langflow-cli env` command group, covering all environment/profile management operations.

#### Test Classes

1. **`TestEnvRegister`** - Tests for `env register` command
   - ✅ Registering a new profile with URL and API key
   - ✅ Validation of required options (URL and API key)
   - ✅ Error handling when registration fails
   - ✅ Setting first profile as default automatically

2. **`TestEnvList`** - Tests for `env list` command
   - ✅ Listing profiles when none exist (empty state)
   - ✅ Listing profiles with existing data
   - ✅ Displaying default profile indicator
   - ✅ Error handling when listing fails

3. **`TestEnvSelect`** - Tests for `env select` command
   - ✅ Selecting an existing profile as default
   - ✅ Error handling for nonexistent profiles
   - ✅ Error handling when setting default fails

4. **`TestEnvCurrent`** - Tests for `env current` command
   - ✅ Displaying current profile information
   - ✅ Showing URL and masked API key
   - ✅ Handling case when no default profile is set
   - ✅ Error handling when getting current profile fails

5. **`TestEnvDelete`** - Tests for `env delete` command
   - ✅ Deleting an existing profile
   - ✅ Deleting the default profile (with fallback handling)
   - ✅ Handling deletion when it's the last profile
   - ✅ Error handling for nonexistent profiles
   - ✅ User confirmation prompt (cancellation)
   - ✅ Error handling when deletion fails

6. **`TestEnvVersion`** - Tests for `env version` command
   - ✅ Getting version using default profile
   - ✅ Getting version using a specific profile
   - ✅ Error handling when API call fails
   - ✅ Error handling when API client initialization fails

#### Covered Scenarios

**Success Paths:**
- ✅ All commands execute successfully with valid inputs
- ✅ Profile operations (register, list, select, delete) work correctly
- ✅ Default profile management works as expected
- ✅ API version retrieval works with both default and specific profiles

**Error Handling:**
- ✅ Missing required options
- ✅ Nonexistent profiles
- ✅ Configuration file errors
- ✅ API client errors
- ✅ Network/API errors

**Edge Cases:**
- ✅ Empty profile list
- ✅ First profile becomes default automatically
- ✅ Deleting the default profile
- ✅ Deleting the last remaining profile
- ✅ User cancellation of destructive operations

**User Interactions:**
- ✅ Confirmation prompts for destructive operations
- ✅ Proper handling of user input (confirm/cancel)

## Test Fixtures

Shared test fixtures are defined in `conftest.py`:

- **`runner`** - Click test runner for invoking CLI commands
- **`mock_config_dir`** - Temporary directory for config files (isolated tests)
- **`mock_profiles`** - Sample profile data for testing
- **`mock_api_client`** - Mock Langflow API client for API-related tests

## Writing New Tests

When adding tests for a new command group:

1. Create a new test file: `test_<command_group>.py`
2. Follow the existing test structure:
   - Import necessary modules (`pytest`, `unittest.mock`, `click.testing`)
   - Create test classes for each command
   - Use descriptive test method names starting with `test_`
   - Add docstrings explaining what each test does
3. Use fixtures from `conftest.py` when possible
4. Mock external dependencies (file system, API calls, etc.)
5. Test both success and error paths
6. Test edge cases and user interactions

### Example Test Structure

```python
"""Tests for <command group> commands."""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from langflow_cli.cli import cli


class TestCommandName:
    """Tests for the '<command group> <command>' command."""
    
    def test_command_success(self, runner):
        """Test successful command execution."""
        with patch("langflow_cli.commands.module.function") as mock_func:
            result = runner.invoke(cli, ["command-group", "command", "--option", "value"])
            
            assert result.exit_code == 0
            mock_func.assert_called_once()
            assert "expected output" in result.output
    
    def test_command_error_handling(self, runner):
        """Test error handling."""
        with patch("langflow_cli.commands.module.function", side_effect=Exception("Error")):
            result = runner.invoke(cli, ["command-group", "command"])
            
            assert result.exit_code != 0
            assert "Error" in result.output
```

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Mocking**: Mock external dependencies (file system, network, etc.) to keep tests fast and isolated
3. **Coverage**: Aim for high test coverage, especially for critical paths
4. **Clarity**: Use descriptive test names and docstrings
5. **Assertions**: Make assertions specific and meaningful
6. **Error Cases**: Always test error handling, not just success paths

## Continuous Integration

Tests should be run as part of CI/CD pipelines. The test suite is designed to:
- Run quickly (mocked dependencies)
- Be deterministic (no reliance on external services)
- Provide clear failure messages
- Generate coverage reports

## Troubleshooting

### Tests Fail with Import Errors

Make sure the package is installed in editable mode:
```bash
uv pip install -e .
```

### Tests Modify Real Configuration

Tests use mocked configuration directories. If you see tests modifying real config:
- Check that `mock_config_dir` fixture is being used
- Verify that patches are correctly applied

### Coverage Report Not Generated

Make sure `pytest-cov` is installed:
```bash
uv pip install -e ".[dev]"
```

## Contributing

When adding new features:
1. Write tests first (TDD approach) or alongside the feature
2. Ensure all tests pass before submitting PR
3. Aim for >80% code coverage
4. Update this README if adding new test patterns or fixtures

