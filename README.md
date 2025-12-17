# Langflow CLI

A command-line tool for managing Langflow environments and resources. This CLI provides an easy way to interact with the Langflow API, manage multiple environments, and work with flows and projects.

## Features

- **Environment Management**: Register and manage multiple Langflow environments/profiles (similar to AWS CLI)
- **Settings**: View Langflow configuration
- **Flow Management**: List, create, update, and delete flows
- **Project Management**: List, create, update, and delete projects
- **Profile Support**: Switch between different environments easily

## Installation

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Install from Source

1. Clone the repository:
```bash
git clone <repository-url>
cd langflow-cli
```

2. Install dependencies and the CLI:
```bash
uv sync
uv pip install -e .
```

3. Verify installation:
```bash
langflow-cli --help
```

## Configuration

The CLI uses an AWS CLI-style configuration approach. Configuration is stored in `~/.langflow-cli/`:

- `~/.langflow-cli/config` - Non-sensitive configuration (URLs, default profile)
- `~/.langflow-cli/credentials` - Sensitive API keys

### Register Your First Environment

```bash
langflow-cli env register prod --url https://api.langflow.org --api-key lf_xxxxxxxxxxxxx
```

This will:
- Create the profile in both config and credentials files
- Set it as the default profile (if it's the first one)

## Usage

### Environment Management

```bash
# Register a new environment
langflow-cli env register <name> --url <url> --api-key <key>

# List all environments
langflow-cli env list

# Select default environment
langflow-cli env select <name>

# Show current environment
langflow-cli env current

# Delete an environment
langflow-cli env delete <name>
```

### Settings

```bash
# Get current configuration
langflow-cli settings get

# Use a specific profile
langflow-cli settings get --profile dev
```

### Flow Management

```bash
# List all flows
langflow-cli flows list

# Get flow details
langflow-cli flows get <flow_id>

# Create a new flow
langflow-cli flows create --name "My Flow" --data '{"description": "A test flow"}'

# Update a flow
langflow-cli flows update <flow_id> --data '{"name": "Updated Name"}'

# Delete a flow
langflow-cli flows delete <flow_id>
```

### Project Management

```bash
# List all projects
langflow-cli projects list

# Get project details
langflow-cli projects get <project_id>

# Create a new project
langflow-cli projects create --name "My Project" --data '{"description": "A test project"}'

# Update a project
langflow-cli projects update <project_id> --data '{"name": "Updated Name"}'

# Delete a project
langflow-cli projects delete <project_id>
```

### Using Different Profiles

All commands support a `--profile` option to override the default profile:

```bash
langflow-cli flows list --profile dev
langflow-cli projects list --profile prod
```

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
└── pyproject.toml
```

## Development

### Setup Development Environment

```bash
uv sync
uv pip install -e .
```

### Running Tests

(Add test instructions when tests are added)

## License

(Add license information)

