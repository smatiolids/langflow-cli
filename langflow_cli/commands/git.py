"""Git-like commands for flow management."""

import json
import re
import click
from typing import Optional, Tuple
from rich.console import Console
from rich.table import Table
from langflow_cli.git_config import (
    add_remote,
    list_remotes,
    remove_remote,
    set_current_remote,
    set_current_branch,
    get_current_remote,
    get_current_branch,
    get_current_selection,
)
from langflow_cli.git_client import GitHubClient
from langflow_cli.api_client import LangflowAPIClient
from langflow_cli.config import get_default_profile
from langflow_cli.utils import print_json, resolve_project_id


console = Console()


@click.group()
def git():
    """Git-like commands for managing flows in GitHub repositories."""
    pass


# Remote Management Commands

@git.group()
def remote():
    """Manage Git remotes (origins)."""
    pass


@remote.command("add")
@click.argument("name")
@click.argument("url")
@click.option("--token", required=True, help="GitHub personal access token (required)")
def remote_add(name: str, url: str, token: str):
    """Register a new remote (origin)."""
    try:
        add_remote(name, url, token)
        console.print(f"[green]✓[/green] Remote '{name}' added successfully")
        console.print(f"[dim]URL: {url}[/dim]")
    except ValueError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to add remote: {str(e)}")
        raise click.Abort()


@remote.command("list")
def remote_list():
    """List all registered remotes."""
    try:
        remotes = list_remotes()
        
        if not remotes:
            console.print("[yellow]No remotes registered.[/yellow]")
            return
        
        table = Table(title="Git Remotes")
        table.add_column("Name", style="cyan")
        table.add_column("URL", style="green")
        
        for name, config in remotes.items():
            table.add_row(
                name,
                config["url"]
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to list remotes: {str(e)}")
        raise click.Abort()


@remote.command("remove")
@click.argument("name")
def remote_remove(name: str):
    """Remove a remote."""
    try:
        remove_remote(name)
        console.print(f"[green]✓[/green] Remote '{name}' removed successfully")
    except ValueError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to remove remote: {str(e)}")
        raise click.Abort()


@remote.command("select")
@click.argument("name")
@click.argument("branch", required=False)
@click.option("--profile", help="Profile to use (overrides default)")
def remote_select(name: str, branch: Optional[str], profile: Optional[str]):
    """Set the active remote (origin). Optionally select a branch at the same time.
    
    Examples:
        langflow-cli git remote select origin
        langflow-cli git remote select origin main
    """
    try:
        profile_name = profile or get_default_profile()
        if not profile_name:
            raise ValueError("No profile selected. Use 'langflow-cli env register' to create one.")
        
        # Check if there's a current branch before changing remote
        current_branch = get_current_branch(profile_name)
        current_remote = get_current_remote(profile_name)
        
        # Verify remote exists
        from langflow_cli.git_config import get_remote
        get_remote(name)
        
        set_current_remote(profile_name, name)
        console.print(f"[green]✓[/green] Remote '{name}' selected for profile '{profile_name}'")
        
        # If branch is provided, verify it exists and set it
        if branch:
            from langflow_cli.git_client import GitHubClient
            client = GitHubClient(name)
            branches = client.get_branches()
            
            if branch not in branches:
                console.print(f"[red]✗[/red] Branch '{branch}' not found in remote '{name}'")
                console.print(f"[yellow]Available branches: {', '.join(branches)}[/yellow]")
                raise click.Abort()
            
            set_current_branch(profile_name, branch)
            console.print(f"[green]✓[/green] Branch '{branch}' selected")
        else:
            # Inform user if branch was reset (only if no branch was provided)
            if current_branch and current_remote != name:
                console.print(f"[yellow]Note: Branch '{current_branch}' was reset. Use 'langflow-cli git checkout <branch>' to select a branch.[/yellow]")
    except ValueError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to select remote: {str(e)}")
        raise click.Abort()


# Branch Management Commands

@git.command("branch")
@click.argument("action", type=click.Choice(["list"]))
@click.option("--remote", help="Remote name (overrides current selection)")
@click.option("--profile", help="Profile to use (overrides default)")
def branch(action: str, remote: Optional[str], profile: Optional[str]):
    """List available branches."""
    try:
        profile_name = profile or get_default_profile()
        if not profile_name:
            raise ValueError("No profile selected. Use 'langflow-cli env register' to create one.")
        
        remote_name = remote or get_current_remote(profile_name)
        if not remote_name:
            raise ValueError("No remote selected. Use 'langflow-cli git remote select <name>' first.")
        
        client = GitHubClient(remote_name)
        branches = client.get_branches()
        
        if not branches:
            console.print("[yellow]No branches found.[/yellow]")
            return
        
        current_branch = get_current_branch(profile_name)
        
        table = Table(title=f"Branches in {remote_name}")
        table.add_column("Branch", style="cyan")
        table.add_column("Status", style="green")
        
        for branch_name in sorted(branches):
            status = "← current" if branch_name == current_branch else ""
            table.add_row(branch_name, status)
        
        console.print(table)
    except ValueError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to list branches: {str(e)}")
        raise click.Abort()


@git.command("checkout")
@click.argument("branch_name")
@click.option("--remote", help="Remote name (overrides current selection)")
@click.option("--profile", help="Profile to use (overrides default)")
def checkout(branch_name: str, remote: Optional[str], profile: Optional[str]):
    """Select/checkout a branch."""
    try:
        profile_name = profile or get_default_profile()
        if not profile_name:
            raise ValueError("No profile selected. Use 'langflow-cli env register' to create one.")
        
        remote_name = remote or get_current_remote(profile_name)
        if not remote_name:
            raise ValueError("No remote selected. Use 'langflow-cli git remote select <name>' first.")
        
        # Verify branch exists
        client = GitHubClient(remote_name)
        branches = client.get_branches()
        
        if branch_name not in branches:
            console.print(f"[red]✗[/red] Branch '{branch_name}' not found")
            console.print(f"[yellow]Available branches: {', '.join(branches)}[/yellow]")
            raise click.Abort()
        
        set_current_branch(profile_name, branch_name)
        console.print(f"[green]✓[/green] Switched to branch '{branch_name}'")
    except ValueError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to checkout branch: {str(e)}")
        raise click.Abort()


# Push/Pull Commands

@git.command("push")
@click.option("--flow-id", help="Flow ID to push")
@click.option("--project-id", help="Project ID to push (pushes all flows in the project)")
@click.option("--project-name", help="Project name to push (pushes all flows in the project)")
@click.option("--project-only", is_flag=True, help="When pushing a project, push only project.json (metadata only)")
@click.option("--remote", help="Remote name (overrides current selection)")
@click.option("--branch", help="Branch name (overrides current selection)")
@click.option("--message", "-m", help="Commit message")
@click.option("--profile", help="Profile to use (overrides default)")
def push(
    flow_id: Optional[str],
    project_id: Optional[str],
    project_name: Optional[str],
    project_only: bool,
    remote: Optional[str],
    branch: Optional[str],
    message: Optional[str],
    profile: Optional[str]
):
    """Push a flow or project to GitHub repository."""
    try:
        # Validate that exactly one option is provided
        options_count = sum(1 for x in [flow_id, project_id, project_name] if x)
        if options_count == 0:
            raise ValueError("Must specify one of: --flow-id, --project-id, or --project-name")
        if options_count > 1:
            raise ValueError("Can only specify one of: --flow-id, --project-id, or --project-name")
        
        # Validate that --project-only is only used with project options
        if project_only and flow_id:
            raise ValueError("--project-only can only be used with --project-id or --project-name")
        
        profile_name = profile or get_default_profile()
        if not profile_name:
            raise ValueError("No profile selected. Use 'langflow-cli env register' to create one.")
        
        # Get remote and branch
        remote_name = remote or get_current_remote(profile_name)
        if not remote_name:
            raise ValueError("No remote selected. Use 'langflow-cli git remote select <name>' first.")
        
        branch_name = branch or get_current_branch(profile_name)
        if not branch_name:
            raise ValueError("No branch selected. Use 'langflow-cli git checkout <branch>' first.")
        
        # Initialize clients
        langflow_client = LangflowAPIClient(profile_name=profile_name)
        github_client = GitHubClient(remote_name)
        
        # Determine what to push
        if flow_id:
            # Push single flow
            _push_flow(langflow_client, github_client, flow_id, remote_name, branch_name, message)
        else:
            # Push project (all flows or metadata only)
            resolved_project_id = resolve_project_id(project_id, project_name, langflow_client)
            
            if not resolved_project_id:
                raise ValueError("Must specify either --project-id or --project-name when pushing a project")
            
            _push_project(langflow_client, github_client, resolved_project_id, remote_name, branch_name, message, project_only)
        
    except ValueError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to push: {str(e)}")
        raise click.Abort()


def _get_project_folder(project_name: Optional[str], project_id: Optional[str]) -> str:
    """
    Generate project folder name using pattern: <project_name>[<project_id>].
    
    Args:
        project_name: Name of the project (optional)
        project_id: ID of the project (optional)
        
    Returns:
        Project folder name in format: <sanitized_project_name>[<project_id>] or "_no_project" if no project
    """
    if project_name and project_id:
        sanitized_project = GitHubClient.sanitize_name(project_name)
        project_id_str = str(project_id)
        return f"projects/{sanitized_project}"
    else:
        return "projects/_no_project"


def _get_project_file_path(project_name: Optional[str], project_id: Optional[str]) -> str:
    """
    Generate full project file path using pattern: <project_folder>/<project_name>[<project_id>].json.
    
    Args:
        project_name: Name of the project (optional)
        project_id: ID of the project (optional)
        
    Returns:
        Full project file path in format: <project_folder>/<project_name>[<project_id>].json
        or "_no_project/project.json" if no project
    """
    project_folder = _get_project_folder(project_name, project_id)
    
    return f"{project_folder}/project.json"
   

def _push_flow_to_github(
    flow: dict,
    flow_id: str,
    project_folder: str,
    github_client: GitHubClient,
    branch_name: str,
    message: Optional[str],
    verbose: bool = True
) -> Tuple[bool, bool]:
    """
    Push a flow object to GitHub repository.
    
    Args:
        flow: Flow dictionary object
        flow_id: Flow ID string
        project_folder: Project folder name
        github_client: GitHub client instance
        branch_name: Branch name
        message: Optional commit message
        verbose: Whether to print verbose messages
        
    Returns:
        Tuple of (was_pushed, was_skipped)
    """
    flow_name = flow.get("name", "Unnamed")
    sanitized_flow = GitHubClient.sanitize_name(flow_name)
    flow_id_str = str(flow_id)
    file_path = f"{project_folder}/{sanitized_flow}_{flow_id_str}.json"
    
    # Serialize flow to JSON
    flow_json = json.dumps(flow, indent=2, ensure_ascii=False, default=str)
    
    # Check if file exists and compare content
    if verbose:
        console.print(f"[cyan]Checking flow in {branch_name}...[/cyan]")
    if github_client.file_exists(file_path, branch_name):
        try:
            existing_content = github_client.get_file(file_path, branch_name)
            # Normalize both JSONs for comparison (parse and re-serialize)
            existing_flow = json.loads(existing_content)
            # Compare normalized JSON objects
            if json.dumps(existing_flow, sort_keys=True, default=str) == json.dumps(flow, sort_keys=True, default=str):
                if verbose:
                    console.print(f"[yellow]⏭[/yellow] Flow unchanged, skipping: {flow_name} at {file_path}")
                return (False, True, file_path)  # Not pushed, skipped
        except Exception as e:
            # If we can't read or compare, proceed with push
            if verbose:
                console.print(f"[yellow]Warning: Could not compare with existing file, proceeding with push: {str(e)}[/yellow]")
    
    # Create commit message
    commit_message = message or f"Push flow: {flow_name}"
    
    # Push to GitHub
    if verbose:
        console.print(f"[cyan]Pushing flow to {branch_name}...[/cyan]")
    github_client.create_or_update_file(file_path, flow_json, commit_message, branch_name)
    
    return (True, False, file_path)  # Pushed, not skipped


def _push_flow(
    langflow_client: LangflowAPIClient,
    github_client: GitHubClient,
    flow_id: str,
    remote_name: str,
    branch_name: str,
    message: Optional[str]
) -> None:
    """Push a single flow to GitHub."""
    # Get Langflow flow
    flow = langflow_client.get_flow(flow_id)
    
    # Get project information
    project_id = flow["project_id"]
    project_name = flow["project_name"]
    
    # Get project folder using standardized pattern
    project_folder = _get_project_folder(project_name, project_id)
    
    # Push flow using shared logic
    was_pushed, was_skipped, file_path = _push_flow_to_github(
        flow, flow_id, project_folder, github_client, branch_name, message, verbose=True
    )
    
    if was_skipped:
        return
    
    console.print(f"[green]✓[/green] Flow pushed successfully")
    console.print(f"[dim]File: {file_path}[/dim]")
    if project_name:
        console.print(f"[dim]Project: {project_name}[/dim]")
    else:
        console.print(f"[yellow]Note: Flow has no project association[/yellow]")
    console.print(f"[dim]Branch: {branch_name}[/dim]")


def _push_project(
    langflow_client: LangflowAPIClient,
    github_client: GitHubClient,
    project_id: str,
    remote_name: str,
    branch_name: str,
    message: Optional[str],
    project_only: bool = False
) -> None:
    """Push all flows in a project to GitHub, or only project.json if project_only is True."""
    # Get full project details
    project = langflow_client.get_project(project_id)
    if not project:
        raise ValueError(f"Project not found: {project_id}")
    
    project_name = project.get("name", "Unknown")
    project_folder = _get_project_folder(project_name, project_id)
    
    # Get all flows for this project
    flows_list = langflow_client.list_flows(project_id=project_id)
    
    console.print(f"[cyan]Pushing project '{project_name}' to {remote_name}/{branch_name}...[/cyan]")
    
    # Push project.json file (without flows attribute)
    try:
        # Create a copy of project data without flows
        project_data = project.copy()
        project_data.pop("flows", None)  # Remove flows attribute if present
        
        # Serialize project to JSON
        project_json = json.dumps(project_data, indent=2, ensure_ascii=False, default=str)
        
        # Create file path for project using standardized pattern
        project_file_path = _get_project_file_path(project_name, project_id)
        
        # Check if project.json exists and compare content
        if github_client.file_exists(project_file_path, branch_name):
            try:
                existing_content = github_client.get_file(project_file_path, branch_name)
                # Normalize both JSONs for comparison (parse and re-serialize)
                existing_project = json.loads(existing_content)
                # Compare normalized JSON objects
                if json.dumps(existing_project, sort_keys=True, default=str) == json.dumps(project_data, sort_keys=True, default=str):
                    console.print(f"[yellow]⏭[/yellow] Skipped (unchanged): project.json")
                else:
                    # Create commit message for project.json
                    project_commit_message = message or f"Push project: {project_name}"
                    
                    # Push project.json to GitHub
                    github_client.create_or_update_file(project_file_path, project_json, project_commit_message, branch_name)
                    console.print(f"[green]✓[/green] Pushed: project.json")
            except Exception:
                # If we can't read or compare, proceed with push
                project_commit_message = message or f"Push project: {project_name}"
                github_client.create_or_update_file(project_file_path, project_json, project_commit_message, branch_name)
                console.print(f"[green]✓[/green] Pushed: project.json")
        else:
            # File doesn't exist, push it
            project_commit_message = message or f"Push project: {project_name}"
            github_client.create_or_update_file(project_file_path, project_json, project_commit_message, branch_name)
            console.print(f"[green]✓[/green] Pushed: project.json")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to push project.json: {str(e)}")
        # Continue with flows even if project.json fails
    
    # Push flows only if project_only is False
    if project_only:
        console.print(f"\n[green]✓[/green] Project metadata push completed")
        console.print(f"[dim]Project: {project_name}[/dim]")
        console.print(f"[dim]Branch: {branch_name}[/dim]")
        return
    
    # Push all flows
    if not flows_list:
        console.print(f"[yellow]No flows found in project '{project_name}'.[/yellow]")
        console.print(f"\n[green]✓[/green] Project push completed")
        console.print(f"[dim]Project: {project_name}[/dim]")
        console.print(f"[dim]Branch: {branch_name}[/dim]")
        return
    
    console.print(f"[cyan]Pushing {len(flows_list)} flow(s)...[/cyan]")
    
    pushed_count = 0
    skipped_count = 0
    for flow in flows_list:
        flow_id = flow.get("id", flow.get("flow_id", "N/A"))
        flow_name = flow.get("name", "Unnamed")
        
        try:
            # Push flow using shared logic from _push_flow
            was_pushed, was_skipped, file_path = _push_flow_to_github(
                flow, flow_id, project_folder, github_client, branch_name, message, verbose=False
            )
            
            if was_skipped:
                skipped_count += 1
                console.print(f"[yellow]⏭[/yellow] Skipped (unchanged): {flow_name}")
            elif was_pushed:
                pushed_count += 1
                console.print(f"[green]✓[/green] Pushed: {flow_name} to {file_path}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to push flow '{flow_name}': {str(e)}")
            # Continue with other flows
    
    total_processed = pushed_count + skipped_count
    summary_parts = [f"{pushed_count} pushed"]
    if skipped_count > 0:
        summary_parts.append(f"{skipped_count} skipped (unchanged)")
    summary = ", ".join(summary_parts)
    
    console.print(f"\n[green]✓[/green] Project push completed: {summary} out of {len(flows_list)} flows")
    console.print(f"[dim]Project: {project_name}[/dim]")
    console.print(f"[dim]Branch: {branch_name}[/dim]")


def _pull_flow(
    langflow_client: LangflowAPIClient,
    flow_data: dict,
    resolved_project_id: Optional[str],
    ignore_version_check: bool,
    flow_name_display: Optional[str] = None,
    silent: bool = False
) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Pull a single flow to Langflow (create or update).
    
    Args:
        langflow_client: Langflow API client
        flow_data: Flow data dictionary
        resolved_project_id: Project ID to associate the flow with
        ignore_version_check: Whether to ignore version mismatch warnings
        flow_name_display: Display name for the flow (for messages)
        silent: If True, don't print version mismatch prompts (returns skipped status)
        
    Returns:
        Tuple of (success, result_dict, error_message)
        - success: True if flow was pulled, False if skipped or failed
        - result_dict: Flow result dictionary if successful, None otherwise
        - error_message: Error message if failed, None otherwise
    """
    # Set project association
    if resolved_project_id:
        flow_data["folder_id"] = resolved_project_id
    
    flow_id = flow_data.get("id") or flow_data.get("flow_id")
    flow_name = flow_data.get("name", "Unnamed")
    display_name = flow_name_display or flow_name
    
    # Check version compatibility
    if "last_tested_version" in flow_data and not ignore_version_check:
        version_info = langflow_client.get_version()
        current_version = version_info.get("version")
        last_tested = flow_data.get("last_tested_version")
        
        if current_version and last_tested:
            current_version_str = str(current_version).strip()
            last_tested_str = str(last_tested).strip()
            
            if current_version_str != last_tested_str:
                if silent:
                    # In silent mode, skip the flow
                    return (False, None, None)
                
                console.print(
                    f"\n[yellow]⚠[/yellow]  Version mismatch for flow '{display_name}':\n"
                    f"  Flow was tested with version: [cyan]{last_tested_str}[/cyan]\n"
                    f"  Current environment version: [cyan]{current_version_str}[/cyan]\n"
                )
                if not click.confirm("Continue with flow pull?"):
                    return (False, None, None)  # Skipped
    
    # Create or update flow
    existing_flow = None
    try:
        console.print(f"[cyan]Getting flow '{flow_id}' from Langflow...[/cyan]")
        existing_flow = langflow_client.get_flow(flow_id)
    except Exception as e:
        # Flow not found, continue 
        pass
    
    if existing_flow:
        try:
            # Check folders
            if existing_flow["folder_id"] != resolved_project_id:
                console.print(f"[yellow]Flow {flow_id} is not in project {resolved_project_id}. Flow will be moved.[/yellow]")
                if not click.confirm("Continue with flow pull?"):
                    return (False, None, None)  # Skipped

            # Update existing flow
            result = langflow_client.update_flow(flow_id, flow_data)

            if not silent:
                console.print(f"[green]✓[/green] Updated: {display_name}")
            return (True, result, None)
        except Exception as e:
            # Failed to update flow
            console.print(f"[red]✗[/red] Failed to update flow '{display_name}': {str(e)}")
            return (False, None, str(e))
    else:
        # Flow doesn't exist, create new one
        console.print(f"[yellow]Flow '{display_name}' not found in Langflow. Creating new flow...[/yellow]")
        result = langflow_client.create_flow(name=display_name, data=flow_data)
        if not silent:
            console.print(f"[green]✓[/green] Created: {display_name}")
        return (True, result, None)


def _pull_project(
    langflow_client: LangflowAPIClient,
    github_client: GitHubClient,
    project_id: Optional[str],
    project_name: Optional[str],
    branch_name: str,
    ignore_version_check: bool
) -> None:
    """Pull a project and all its flows from GitHub repository to Langflow."""
    # List all folders under "projects" directory
    console.print(f"[cyan]Listing projects in repository...[/cyan]")
    project_folders = github_client.list_files_in_directory("projects", branch_name)
    project_folders = [f for f in project_folders if f["type"] == "dir"]
    
    if not project_folders:
        raise ValueError("No projects found in repository")
    
    resolved_project_id = None
    project_folder_name = None
    
    # If searching by project_id, check each project.json to find the matching one
    if project_id:
        console.print(f"[cyan]Searching for project with ID: {project_id}...[/cyan]")
        for folder in project_folders:
            folder_name = folder["name"]
            project_json_path = f"projects/{folder_name}/project.json"
            
            try:
                project_json_content = github_client.get_file(project_json_path, branch_name)
                project_data = json.loads(project_json_content)
                project_data_id = str(project_data.get("id", project_data.get("project_id", "")))
                
                if project_data_id == str(project_id):
                    resolved_project_id = project_id
                    project_folder_name = folder_name
                    console.print(f"[green]✓[/green] Found project folder: {folder_name}")
                    break
            except Exception:
                # Skip folders without project.json or with errors
                continue
        
        if not resolved_project_id:
            raise ValueError(f"Project with ID '{project_id}' not found in repository")
    
    # If searching by project_name, match by folder name
    elif project_name:
        console.print(f"[cyan]Searching for project with name: {project_name}...[/cyan]")
        sanitized_search_name = GitHubClient.sanitize_name(project_name)
        
        for folder in project_folders:
            folder_name = folder["name"]
            if folder_name == sanitized_search_name:
                project_folder_name = folder_name
                # Get project.json to get the project_id
                project_json_path = f"projects/{folder_name}/project.json"
                try:
                    project_json_content = github_client.get_file(project_json_path, branch_name)
                    project_data = json.loads(project_json_content)
                    resolved_project_id = project_data.get("id", project_data.get("project_id"))
                    console.print(f"[green]✓[/green] Found project folder: {folder_name}")
                    break
                except Exception as e:
                    raise ValueError(f"Failed to read project.json from folder '{folder_name}': {str(e)}")
        
        if not resolved_project_id:
            raise ValueError(f"Project with name '{project_name}' not found in repository")
    else:
        raise ValueError("Must specify either --project-id or --project-name")
    
    # Get project.json
    project_json_path = f"projects/{project_folder_name}/project.json"
    console.print(f"[cyan]Reading project.json from {project_json_path}...[/cyan]")
    project_json_content = github_client.get_file(project_json_path, branch_name)
    project_data = json.loads(project_json_content)
    
    # Remove flows attribute if present (we don't want to include flows when creating/updating)
    project_data.pop("flows", None)
    project_name_from_json = project_data.get("name", "Unknown")
    
    # Check if project exists in Langflow
    existing_project = None
    try:
        existing_project = langflow_client.get_project(resolved_project_id) if resolved_project_id else None
    except Exception as e:
        console.print(f"[yellow]Project {resolved_project_id} not found in Langflow[/yellow]")
    
    if existing_project:
        # Update existing project
        console.print(f"[cyan]Updating project '{project_name_from_json}' in Langflow...[/cyan]")
        # Remove id/project_id as we're updating
        project_data.pop("id", None)
        project_data.pop("project_id", None)
        updated_project = langflow_client.update_project(resolved_project_id, project_data)
        console.print(f"[green]✓[/green] Project '{project_name_from_json}' updated successfully")
    else:
        # Create new project
        console.print(f"[cyan]Creating project '{project_name_from_json}'...[/cyan]")
        # Remove id/project_id as the API will assign a new one
        project_data.pop("id", None)
        project_data.pop("project_id", None)
        created_project = langflow_client.create_project(project_name_from_json, project_data)
        resolved_project_id = created_project.get("id", created_project.get("project_id"))
        console.print(f"[green]✓[/green] Project '{project_name_from_json}' created successfully")
    
    # Get all flow files from the project folder
    console.print(f"[cyan]Listing flows in project folder...[/cyan]")
    flow_files = github_client.list_files_in_directory(f"projects/{project_folder_name}", branch_name)
    flow_files = [f for f in flow_files if f["type"] == "file" and f["name"] != "project.json" and f["name"].endswith(".json")]
    
    if not flow_files:
        console.print(f"[yellow]No flows found in project '{project_name_from_json}'.[/yellow]")
        return
    
    console.print(f"[cyan]Pulling {len(flow_files)} flow(s)...[/cyan]")
    
    pulled_count = 0
    skipped_count = 0
    error_count = 0
    
    for flow_file in flow_files:
        flow_file_path = flow_file["path"]
        flow_name = flow_file["name"]
        
        try:
            # Get flow from GitHub
            flow_json = github_client.get_file(flow_file_path, branch_name)
            flow_data = json.loads(flow_json)
            
            # Pull flow using shared logic
            success, result, error_msg = _pull_flow(
                langflow_client,
                flow_data,
                resolved_project_id,
                ignore_version_check,
                flow_name_display=flow_data.get("name", flow_name),
                silent=False  # Use silent mode for batch operations
            )
            
            if success:
                pulled_count += 1
            elif error_msg:
                error_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            error_count += 1
            console.print(f"[red]✗[/red] Failed to pull flow '{flow_name}': {str(e)}")
            # Continue with other flows
    
    summary_parts = [f"{pulled_count} pulled"]
    if skipped_count > 0:
        summary_parts.append(f"{skipped_count} skipped")
    if error_count > 0:
        summary_parts.append(f"{error_count} errors")
    summary = ", ".join(summary_parts)
    
    console.print(f"\n[green]✓[/green] Project pull completed: {summary} out of {len(flow_files)} flows")
    console.print(f"[dim]Project: {project_name_from_json}[/dim]")
    console.print(f"[dim]Branch: {branch_name}[/dim]")


@git.command("pull")
@click.argument("path", metavar="PATH", required=False)
@click.option("--flow-id", help="Flow ID to pull")
@click.option("--project-id", help="Project ID to pull (pulls all flows in the project)")
@click.option("--project-name", help="Project name to pull (pulls all flows in the project)")
@click.option("--remote", help="Remote name (overrides current selection)")
@click.option("--branch", help="Branch name (overrides current selection)")
@click.option("--profile", help="Profile to use (overrides default)")
@click.option("--ignore-version-check", is_flag=True, help="Ignore version mismatch warning")
def pull(
    path: Optional[str],
    flow_id: Optional[str],
    project_id: Optional[str],
    project_name: Optional[str],
    remote: Optional[str],
    branch: Optional[str],
    profile: Optional[str],
    ignore_version_check: bool
):
    """Pull a flow or project from GitHub repository to Langflow.
    
    Can pull:
    - A single flow by path: PATH (e.g., 'projects/ProjectName/FlowName_flow_id.json')
    - A single flow by ID: --flow-id
    - A project with all flows: --project-id or --project-name
    """
    try:
        profile_name = profile or get_default_profile()
        if not profile_name:
            raise ValueError("No profile selected. Use 'langflow-cli env register' to create one.")
        
        # Get remote and branch
        remote_name = remote or get_current_remote(profile_name)
        if not remote_name:
            raise ValueError("No remote selected. Use 'langflow-cli git remote select <name>' first.")
        
        branch_name = branch or get_current_branch(profile_name)
        if not branch_name:
            raise ValueError("No branch selected. Use 'langflow-cli git checkout <branch>' first.")
        
        # Initialize clients
        github_client = GitHubClient(remote_name)
        langflow_client = LangflowAPIClient(profile_name=profile_name)
        
        # Determine what to pull
        options_count = sum(1 for x in [path, flow_id, project_id, project_name] if x)
        if options_count == 0:
            raise ValueError("Must specify one of: PATH, --flow-id, --project-id, or --project-name")
        if options_count > 1:
            raise ValueError("Can only specify one of: PATH, --flow-id, --project-id, or --project-name")
        
        # Route to appropriate pull function
        if project_id or project_name:
            # Pull entire project
            _pull_project(langflow_client, github_client, project_id, project_name, branch_name, ignore_version_check)
        elif flow_id:
            # Pull by flow ID - need to find the flow file first
            raise ValueError("Pulling by --flow-id is not yet implemented. Use PATH instead.")
        elif path:
            # Pull by path (existing flow pull logic)
            _pull_flow_by_path(langflow_client, github_client, path, project_id, project_name, branch_name, ignore_version_check)
        else:
            raise ValueError("Must specify one of: PATH, --flow-id, --project-id, or --project-name")
        
    except ValueError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to pull: {str(e)}")
        raise click.Abort()


def _pull_flow_by_path(
    langflow_client: LangflowAPIClient,
    github_client: GitHubClient,
    file_path: str,
    project_id: Optional[str],
    project_name: Optional[str],
    branch_name: str,
    ignore_version_check: bool
) -> None:
    """Pull a single flow from GitHub repository to Langflow by file path."""
    # Get file from GitHub
    console.print(f"[cyan]Pulling flow from {file_path}...[/cyan]")
    flow_json = github_client.get_file(file_path, branch_name)
    flow_data = json.loads(flow_json)
    
    # Resolve project
    resolved_project_id = resolve_project_id(project_id, project_name, langflow_client)
    
    # If resolved_project_id is None, try to infer from file path or flow_data
    if not resolved_project_id:
        projects_list = langflow_client.list_projects()
        # Try to infer from file path (project folder name)
        path_parts = file_path.split("/")
        if len(path_parts) > 1:
            # Extract project folder (should be "projects/ProjectName")
            if path_parts[0] == "projects" and len(path_parts) > 1:
                project_folder_name = path_parts[1]
                # Try to find project by matching sanitized name
                for project in projects_list:
                    sanitized = GitHubClient.sanitize_name(project.get("name", ""))
                    if sanitized == project_folder_name:
                        resolved_project_id = project.get("id", project.get("project_id"))
                        break
    
    # If still no project, use the one from flow_data
    if not resolved_project_id:
        resolved_project_id = flow_data.get("folder_id") or flow_data.get("project_id")
    
    # Check if project exists, if not, try to create it from project.json
    if resolved_project_id:
        project = langflow_client.get_project(resolved_project_id)
        if not project:
            # Project doesn't exist, try to create it from project.json
            console.print(f"[yellow]Project {resolved_project_id} not found. Attempting to create from project.json...[/yellow]")
            # Extract project folder from path
            path_parts = file_path.split("/")
            if len(path_parts) > 1 and path_parts[0] == "projects":
                project_folder_name = path_parts[1]
                project_json_path = f"projects/{project_folder_name}/project.json"
                try:
                    project_data = github_client.get_file(project_json_path, branch_name)
                    project_data = json.loads(project_data)
                    project_data.pop("flows", None)
                    project_data.pop("id", None)
                    project_data.pop("project_id", None)
                    project_name_from_json = project_data.get("name")
                    if not project_name_from_json:
                        raise ValueError("Project name not found in project.json")
                    created_project = langflow_client.create_project(project_name_from_json, project_data)
                    resolved_project_id = created_project.get("id", created_project.get("project_id"))
                    console.print(f"[green]✓[/green] Project '{project_name_from_json}' created successfully")
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not create project from project.json: {str(e)}[/yellow]")
                    resolved_project_id = None
    
    # Pull flow using shared logic
    success, result, error_msg = _pull_flow(
        langflow_client,
        flow_data,
        resolved_project_id,
        ignore_version_check,
        flow_name_display=None,  # Will use flow name from flow_data
        silent=False  # Show all messages for single flow pull
    )
    
    if not success:
        if error_msg:
            raise ValueError(f"Failed to pull flow: {error_msg}")
        else:
            # Skipped due to version check
            raise click.Abort()
    
    # Display result (only if we have a result)
    if result:
        projects_list = langflow_client.list_projects()
        result_id = result.get("id", result.get("flow_id", "N/A"))
        result_name = result.get("name", "N/A")
        result_project_id = result.get("folder_id", result.get("project_id", "N/A"))
        
        # Get project name
        result_project_name = "N/A"
        if result_project_id and result_project_id != "N/A":
            project = next(
                (p for p in projects_list if p.get("id", p.get("project_id")) == result_project_id),
                None
            )
            if project:
                result_project_name = project.get("name", "N/A")
        
        filtered_result = {
            "id": result_id,
            "name": result_name,
            "project_id": result_project_id,
            "project_name": result_project_name
        }
        
        print_json(filtered_result, console)

