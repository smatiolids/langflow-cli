# Development Guide

This guide is for developers who want to contribute to or build from source.

## Installation Methods

### Option 1: Install from Source (Development)

1. Clone the repository:
```bash
git clone https://github.com/smatiolids/langflow-cli.git
cd langflow-cli
```

2. Install dependencies and the CLI:
```bash
uv sync
uv pip install -e .
```

Or with pip:
```bash
pip install -e .
```

3. Verify installation:
```bash
langflow-cli --help
```

### Option 2: Install from Git Repository

Install directly from a git repository:
```bash
# Using uv
uv pip install git+https://github.com/smatiolids/langflow-cli.git

# Using pip
pip install git+https://github.com/smatiolids/langflow-cli.git

# Install from a specific branch or tag
pip install git+https://github.com/smatiolids/langflow-cli.git@main
pip install git+https://github.com/smatiolids/langflow-cli.git@v0.1.0
```

### Option 3: Build and Install from Distribution Package

1. Build the distribution package:
```bash
# Using uv
uv build

# Using pip
pip install build
python -m build
```

This creates distribution files in the `dist/` directory (`.whl` and `.tar.gz` files).

2. Install from the built package:
```bash
# Install from wheel (recommended)
uv pip install dist/langflow_cli-*.whl

# Or using pip
pip install dist/langflow_cli-*.whl

# Or install from source distribution
pip install dist/langflow-cli-*.tar.gz
```

3. Distribute the package:
   - Share the `dist/` directory files with others
   - They can install using: `pip install langflow_cli-*.whl`

### Option 4: Publish to PyPI (Public Distribution)

See [PUBLISHING.md](PUBLISHING.md) for detailed instructions on publishing to PyPI.

### Option 5: Install with uv tool (Global Tool)

If using `uv` as a tool manager:
```bash
uv tool install git+https://github.com/smatiolids/langflow-cli.git
```

The command will be available at `~/.local/bin/langflow-cli`.

## Project Structure

```
langflow-cli/
├── langflow_cli/
│   ├── __init__.py
│   ├── cli.py                 # Main CLI entry point
│   ├── config.py              # Configuration management
│   ├── api_client.py          # Langflow API client
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── env.py             # Environment management commands
│   │   ├── settings.py        # Settings commands
│   │   ├── flows.py           # Flow commands
│   │   └── projects.py        # Project commands
│   └── utils.py               # Utility functions
├── README.md
├── DEVELOPING.md
├── PUBLISHING.md
├── LICENSE
└── pyproject.toml
```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/smatiolids/langflow-cli.git
cd langflow-cli

# Create virtual environment and install dependencies
uv sync

# Install the package in editable mode
uv pip install -e .
```

### Running Tests

1. **Install test dependencies**:
```bash
# Using uv
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

2. **Run all tests**:
```bash
pytest
```

3. **Run tests for a specific command group**:
```bash
# Run environment command tests
pytest tests/test_env.py

# Run with verbose output
pytest -v tests/test_env.py
```

4. **Run tests with coverage**:
```bash
pytest --cov=langflow_cli --cov-report=html
```

5. **Run a specific test**:
```bash
pytest tests/test_env.py::TestEnvRegister::test_register_new_profile
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

