"""Push command for flows and projects."""

import json
from typing import Optional, Tuple
import click
from rich.console import Console
from langflow_cli.git_config import (
    get_current_remote,
    get_current_branch,
)
from langflow_cli.git_client import GitHubClient
from langflow_cli.api_client import LangflowAPIClient
from langflow_cli.config import get_default_profile
from langflow_cli.utils import resolve_project_id

console = Console()


def register_push_command(git_group: click.Group) -> None:
    """Register push command with the git group."""
    
    @git_group.command("push")
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
) -> Tuple[bool, bool, str]:
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
        Tuple of (was_pushed, was_skipped, file_path)
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
