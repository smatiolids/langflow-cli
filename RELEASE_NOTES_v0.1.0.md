# Langflow CLI v0.1.0 - Initial Release

We're excited to announce the first release of **Langflow CLI**, a command-line tool that makes it easy to manage Langflow environments and resources from your terminal.

## 🎉 What's New

This initial release provides a complete CLI interface for interacting with the Langflow API, featuring environment management, flow operations, and project management.

## ✨ Key Features

### 🔐 Environment Management
- **Multi-environment support**: Register and manage multiple Langflow environments/profiles (similar to AWS CLI)
- **Secure credential storage**: API keys are stored separately from configuration files
- **Easy switching**: Switch between environments with a single command
- **Profile management**: List, select, and delete environments as needed

### 📊 Flow Management
- **List flows**: View all flows with project association
- **Create flows**: Create new flows from JSON data or files
- **Update flows**: Modify existing flows
- **Delete flows**: Remove flows you no longer need
- **Project association**: Associate flows with projects by ID or name
- **Project validation**: Automatic validation of project IDs before flow creation

### 📁 Project Management
- **List projects**: View all available projects
- **Create projects**: Set up new projects
- **Update projects**: Modify project details
- **Delete projects**: Remove projects when needed

### ⚙️ Settings & Configuration
- **View configuration**: Get current Langflow configuration
- **Profile override**: Use `--profile` option on any command to override the default environment

## 🚀 Installation

Install from PyPI:

```bash
pip install langflow-cli
```

Or using `uv`:

```bash
uv pip install langflow-cli
```

## 📖 Quick Start

1. **Register your first environment**:
```bash
langflow-cli env register prod --url https://api.langflow.org --api-key lf_xxxxxxxxxxxxx
```

2. **List your flows**:
```bash
langflow-cli flows list
```

3. **Create a new flow**:
```bash
langflow-cli flows create --name "My Flow" --project-name "My Project"
```

## 🎯 Use Cases

- **Automation**: Integrate Langflow operations into your CI/CD pipelines
- **Multi-environment workflows**: Manage dev, staging, and production environments
- **Bulk operations**: Create and manage multiple flows and projects efficiently
- **Scripting**: Use in shell scripts for automated workflows

## 📋 What's Included

- Complete CLI interface for Langflow API
- AWS CLI-style configuration management
- Support for all major Langflow operations (flows, projects, settings)
- Beautiful terminal output with Rich library
- Comprehensive error handling and validation
- Full documentation and examples

## 🔧 Technical Details

- **Python**: 3.8+
- **Dependencies**: click, requests, rich
- **License**: MIT
- **Package**: Available on PyPI as `langflow-cli`

## 📚 Documentation

- [README.md](README.md) - User guide and usage examples
- [DEVELOPING.md](DEVELOPING.md) - Development setup and contribution guide
- [PUBLISHING.md](PUBLISHING.md) - Publishing instructions

## 🙏 Acknowledgments

Thank you for using Langflow CLI! We hope this tool makes working with Langflow more efficient and enjoyable.

## 🔗 Links

- **Repository**: https://github.com/smatiolids/langflow-cli
- **PyPI**: https://pypi.org/project/langflow-cli/
- **Issues**: https://github.com/smatiolids/langflow-cli/issues

---

**Full Changelog**: This is the initial release. See the repository for all commits.

