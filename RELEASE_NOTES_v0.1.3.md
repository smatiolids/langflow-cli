# Langflow CLI v0.1.3 - Release Notes

We're excited to announce **Langflow CLI v0.1.3**, featuring major enhancements including Git integration, status monitoring, version checking, and improved error handling.

## 🎉 What's New

This release introduces powerful Git integration capabilities, allowing you to seamlessly sync flows between Langflow and GitHub repositories. We've also added a status command for quick configuration overview, automatic version checking, and enhanced error handling.

## ✨ Key Features

### 🔄 Git Integration (NEW)
- **Push flows to GitHub**: Push individual flows or entire projects to GitHub repositories
- **Pull flows from GitHub**: Import flows from GitHub repositories into Langflow
- **Project-based organization**: Flows are automatically organized by project folders in repositories
- **Remote management**: Register and manage multiple Git remotes (supports GitHub, GitHub Enterprise, HTTPS, and SSH)
- **Branch management**: Select and switch between branches easily
- **Profile-based Git config**: Each environment profile can have its own remote and branch selection
- **Flexible push options**: Push single flows, entire projects, or project metadata only
- **Custom commit messages**: Add descriptive commit messages when pushing flows

### 📊 Status Command (NEW)
- **Quick overview**: View current environment and Git configuration at a glance
- **Profile-aware**: Check status for any profile with `--profile` option
- **Comprehensive display**: Shows environment name, API URL, API key (masked), Git remote, and branch

### ✅ Version Checking (NEW)
- **Automatic validation**: CLI automatically checks if flow's `last_tested_version` matches the current Langflow environment version
- **Safety warnings**: Prompts for confirmation when version mismatches are detected
- **Override option**: Use `--ignore-version-check` flag to skip version validation when needed
- **Prevents compatibility issues**: Helps ensure flows are compatible with your Langflow environment

### 🛠️ Project Management Enhancements
- **List flows by project**: Filter and view all flows within a specific project
- **Project export**: Export entire projects as zip files containing project metadata and all flows
- **Enhanced project validation**: Improved validation when associating flows with projects

### 🔒 Improved Error Handling
- **Better SSL error messages**: More helpful error messages with protocol mismatch hints
- **Enhanced testing framework**: Improved test coverage and documentation
- **Graceful error handling**: Better error messages throughout the CLI

### 📝 Documentation Improvements
- **Comprehensive Git workflow examples**: Detailed examples for Git push/pull operations
- **Enhanced README**: Updated with all new features and usage examples
- **Better remote selection instructions**: Clearer guidance on configuring Git remotes

## 🚀 Installation

Upgrade to the latest version:

```bash
pip install --upgrade langflow-cli
```

Or using `uv`:

```bash
uv pip install --upgrade langflow-cli
```

## 📖 Quick Start

### Git Integration Example

1. **Register a Git remote**:
```bash
langflow-cli git remote add origin https://github.com/user/flows-repo --token YOUR_TOKEN
```

2. **Select remote and branch**:
```bash
langflow-cli git remote select origin main
```

3. **Push a project to GitHub**:
```bash
langflow-cli git push --project-name "My Project" --message "Initial commit"
```

4. **Pull a flow from GitHub**:
```bash
langflow-cli git pull "My_Project/My_Flow_abc-123-def.json"
```

### Status Command

```bash
# View current status
langflow-cli status

# View status for a specific profile
langflow-cli status --profile dev
```

## 🔄 Migration from v0.1.0

If you're upgrading from v0.1.0:

1. **No breaking changes**: All existing commands work as before
2. **New Git features**: Git integration is optional - configure it when you need it
3. **Version checking**: New version checks are enabled by default but can be skipped with `--ignore-version-check`

## 📋 What's Included

- Complete Git integration for flow synchronization
- Status command for configuration overview
- Automatic version checking for flow compatibility
- Enhanced project management capabilities
- Improved error handling and user feedback
- Comprehensive documentation updates

## 🔧 Technical Details

- **Python**: 3.8+
- **New Dependencies**: PyGithub (for Git operations)
- **Backward Compatible**: All v0.1.0 features remain unchanged
- **License**: MIT

## 🐛 Bug Fixes

- Improved SSL error handling with better error messages
- Enhanced project validation and error reporting
- Fixed issues with remote selection and branch management

## 📚 Documentation

- [README.md](README.md) - Complete user guide with Git integration examples
- [DEVELOPING.md](DEVELOPING.md) - Development setup and contribution guide
- [PUBLISHING.md](PUBLISHING.md) - Publishing instructions

## 🙏 Acknowledgments

Thank you to all contributors and users who provided feedback and helped improve Langflow CLI!

Special thanks to:
- @glenioborges for SSL error handling improvements

## 🔗 Links

- **Repository**: https://github.com/smatiolids/langflow-cli
- **PyPI**: https://pypi.org/project/langflow-cli/
- **Issues**: https://github.com/smatiolids/langflow-cli/issues

---

**Full Changelog**: https://github.com/smatiolids/langflow-cli/compare/v0.1.0...v0.1.3


