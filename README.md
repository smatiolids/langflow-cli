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
- pip or [uv](https://github.com/astral-sh/uv) package manager

### Install from PyPI

The easiest way to install Langflow CLI:

```bash
pip install langflow-cli
```

Or using `uv`:

```bash
uv pip install langflow-cli
```

### Verify Installation

After installation, verify the CLI is available:

```bash
langflow-cli --help
```

### Other Installation Methods

For development or other installation methods (installing from source, git, etc.), see [DEVELOPING.md](DEVELOPING.md).

## Configuration

The CLI uses an AWS CLI-style configuration approach. Configuration is stored in `~/.langflow-cli/`:

- `~/.langflow-cli/config` - Non-sensitive configuration (URLs, default profile)
- `~/.langflow-cli/credentials` - Sensitive API keys

### Register Your First Environment

```bash
langflow-cli env register local_dev --url https://localhost:3000 --api-key YOUR_KEY
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

# Create a new flow with JSON data string
langflow-cli flows create --name "My Flow" --data '{"description": "A test flow"}'

# Create a new flow from a JSON file
langflow-cli flows create --name "My Flow" --file /path/to/flow-data.json

# Create a flow and associate it with a project by ID
langflow-cli flows create --name "My Flow" --project-id "123e4567-e89b-12d3-a456-426614174000"

# Create a flow and associate it with a project by name
langflow-cli flows create --name "My Flow" --project-name "My Project"

# Create a flow from file and associate with a project
langflow-cli flows create --file flow.json --project-name "My Project"

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! For development setup and contribution guidelines, see [DEVELOPING.md](DEVELOPING.md).

