# Langflow CLI

A command-line tool for managing Langflow environments and resources. This CLI provides an easy way to interact with the Langflow API, manage multiple environments, and work with flows and projects.

## Features

- **Environment Management**: Register and manage multiple Langflow environments/profiles (similar to AWS CLI)
- **Status**: View current environment and Git configuration at a glance
- **Settings**: View Langflow configuration
- **Flow Management**: List, create, update, and delete flows
- **Project Management**: List, create, update, and delete projects
- **Git Integration**: Push and pull flows to/from GitHub repositories with project-based organization
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
# or use the shorter alias
lf-cli --help
```

**Note:** The CLI can be called with either `langflow-cli` or `lf-cli` (shorter alias).

### Other Installation Methods

For development or other installation methods (installing from source, git, etc.), see [DEVELOPING.md](DEVELOPING.md).

## Configuration

The CLI uses an AWS CLI-style configuration approach. Configuration is stored in `~/.langflow-cli/`:

- `~/.langflow-cli/config` - Non-sensitive configuration (URLs, default profile)
- `~/.langflow-cli/credentials` - Sensitive API keys
- `~/.langflow-cli/git_config` - Git remote configurations and current selections (remote/branch per profile)

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

# Show current environment version
langflow-cli env version

# Delete an environment
langflow-cli env delete <name>
```

### Status

View the current environment and Git configuration:

```bash
# Show current status (default profile)
langflow-cli status

# Show status for a specific profile
langflow-cli status --profile dev
```

The status command displays:
- Current environment/profile name
- Langflow API URL
- API Key (masked)
- Git Remote name
- Git Remote URL
- Git Branch

### Settings

```bash
# Get current configuration
langflow-cli settings get

# Use a specific profile
langflow-cli settings get --profile dev
```

### Flow Management

When creating flows, the CLI automatically checks if the flow's `last_tested_version` matches the current Langflow environment version. If versions don't match, a warning is displayed and you'll be prompted to confirm before proceeding. Use `--ignore-version-check` to skip this check.

```bash
# List all flows
langflow-cli flows list

# List flows filtered by project ID
langflow-cli flows list --project-id <project_id>

# List flows filtered by project name
langflow-cli flows list --project-name "My Project"

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

# Create a flow and ignore version mismatch warnings
langflow-cli flows create --file flow.json --ignore-version-check

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

# List all flows for a project
langflow-cli projects list-flows <project_id>

# Export a project as a zip file (contains project.json and all flows as JSON files)
langflow-cli projects export <project_id> --file project_backup.zip

# Create a new project
langflow-cli projects create --name "My Project" --data '{"description": "A test project"}'

# Update a project
langflow-cli projects update <project_id> --data '{"name": "Updated Name"}'

# Delete a project
langflow-cli projects delete <project_id>
```

### Git Commands

The Git commands allow you to sync flows between Langflow and GitHub repositories. Flows are automatically organized by project folders in the repository.

**Prerequisites:**
- A GitHub repository
- A GitHub personal access token

**Configuration:**
Git configuration is stored in `~/.langflow-cli/git_config`:
- Remote (origin) configurations
- Current remote and branch selection per profile

#### Remote Management

```bash
# Register a new remote (origin) with HTTPS URL and token
langflow-cli git remote add origin https://github.com/user/flows-repo --token YOUR_TOKEN

# Register a remote with SSH URL and token
langflow-cli git remote add origin git@github.com:user/flows-repo.git --token YOUR_TOKEN

# Register a remote with custom domain (GitHub Enterprise) and token
langflow-cli git remote add origin git@github-ibm:user/flows-repo.git --token YOUR_TOKEN

# Register a remote with HTTPS URL for GitHub Enterprise and token
langflow-cli git remote add origin https://github-ibm.com/user/flows-repo --token YOUR_TOKEN

# List all registered remotes
langflow-cli git remote list

# Remove a remote
langflow-cli git remote remove origin

# Select the active remote for the current profile
langflow-cli git remote select origin

# Select remote and branch in one command
langflow-cli git remote select origin main
```

#### Branch Management

```bash
# List available branches in the repository
langflow-cli git branch list

# List branches for a specific remote
langflow-cli git branch list --remote origin

# Select/checkout a branch
langflow-cli git checkout main

# Checkout a branch for a specific remote
langflow-cli git checkout main --remote origin
```

#### Push/Pull Operations

Flows are stored in the repository organized by project folders using the pattern: `{project_name}[{project_id}]/{flow_name}[{flow_id}].json`. Projects are stored as: `{project_name}[{project_id}]/{project_name}[{project_id}].json`

**Push a flow or project to GitHub:**
```bash
# Push a single flow (uses current remote and branch)
langflow-cli git push --flow-id <flow_id>

# Push a flow with a custom commit message
langflow-cli git push --flow-id <flow_id> --message "Add new flow"

# Push a project (all flows in the project) by project ID
langflow-cli git push --project-id <project_id>

# Push a project by project name
langflow-cli git push --project-name "My Project"

# Push only project.json (metadata) without flows
langflow-cli git push --project-name "My Project" --project-only

# Push to a specific remote and branch
langflow-cli git push --flow-id <flow_id> --remote origin --branch main --message "Update flow"

# Push a project with a custom commit message
langflow-cli git push --project-name "My Project" --message "Update all flows"

# Push only project metadata with a custom message
langflow-cli git push --project-id <project_id> --project-only --message "Update project metadata"

# Note: Flows without a project are stored in the _no_project/ folder
```

**Pull a flow from GitHub:**
```bash
# Pull a flow by full path (required format: ProjectName/FlowName_id.json)
langflow-cli git pull "My_Project/My_Flow_abc-123-def.json"

# Pull and create/update in a specific project
langflow-cli git pull "Other_Project/Some_Flow_xyz.json" --project-name "My Project"

# Pull with project ID
langflow-cli git pull "My_Project/My_Flow_abc-123-def.json" --project-id "123e4567-e89b-12d3-a456-426614174000"

# Pull from a specific remote and branch
langflow-cli git pull "My_Project/My_Flow.json" --remote origin --branch main

# Pull and ignore version mismatch warnings
langflow-cli git pull "My_Project/My_Flow.json" --ignore-version-check
```

**Example workflow:**
```bash
# 1. Register a remote with token
langflow-cli git remote add origin https://github.com/user/flows-repo --token YOUR_TOKEN

# 2. Select remote and branch (can be done in one command or separately)
langflow-cli git remote select origin main

# Or select them separately:
# langflow-cli git remote select origin
# langflow-cli git checkout main

# 3. Push a flow
langflow-cli git push --flow-id abc-123-def --message "Add new flow"

# Or push an entire project
langflow-cli git push --project-name "My Project" --message "Update all flows"

# 4. Pull a flow
langflow-cli git pull "My_Project/My_Flow_abc-123-def.json"
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

