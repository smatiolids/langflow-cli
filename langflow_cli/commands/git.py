"""Git-like commands for flow management."""

import json
import click
from typing import Optional
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
    project_id = flow.get("folder_id") or flow.get("project_id")
    project_name = None
    
    if project_id:
        projects = langflow_client.list_projects()
        project = next((p for p in projects if p.get("id", p.get("project_id")) == project_id), None)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        project_name = project.get("name", "Unknown")
    
    # Sanitize names
    if project_name:
        sanitized_project = GitHubClient.sanitize_name(project_name)
    else:
        sanitized_project = "_no_project"
    
    sanitized_flow = GitHubClient.sanitize_name(flow.get("name", "Unnamed"))
    flow_id_str = str(flow_id)
    
    # Create file path
    file_path = f"{sanitized_project}/{sanitized_flow}_{flow_id_str}.json"
    
    # Serialize flow to JSON
    flow_json = json.dumps(flow, indent=2, ensure_ascii=False, default=str)
    
    # Check if file exists and compare content
    console.print(f"[cyan]Checking flow in {remote_name}/{branch_name}...[/cyan]")
    if github_client.file_exists(file_path, branch_name):
        try:
            existing_content = github_client.get_file(file_path, branch_name)
            # Normalize both JSONs for comparison (parse and re-serialize)
            existing_flow = json.loads(existing_content)
            # Compare normalized JSON objects
            if json.dumps(existing_flow, sort_keys=True, default=str) == json.dumps(flow, sort_keys=True, default=str):
                console.print(f"[yellow]⏭[/yellow] Flow unchanged, skipping: {flow.get('name', flow_id)}")
                console.print(f"[dim]File: {file_path}[/dim]")
                return
        except Exception as e:
            # If we can't read or compare, proceed with push
            console.print(f"[yellow]Warning: Could not compare with existing file, proceeding with push: {str(e)}[/yellow]")
    
    # Create commit message
    commit_message = message or f"Push flow: {flow.get('name', flow_id)}"
    
    # Push to GitHub
    console.print(f"[cyan]Pushing flow to {remote_name}/{branch_name}...[/cyan]")
    github_client.create_or_update_file(file_path, flow_json, commit_message, branch_name)
    
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
    sanitized_project = GitHubClient.sanitize_name(project_name)
    
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
        
        # Create file path for project.json
        project_file_path = f"{sanitized_project}/project.json"
        
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
            sanitized_flow = GitHubClient.sanitize_name(flow_name)
            flow_id_str = str(flow_id)
            
            # Create file path
            file_path = f"{sanitized_project}/{sanitized_flow}_{flow_id_str}.json"
            
            # Serialize flow to JSON
            flow_json = json.dumps(flow, indent=2, ensure_ascii=False, default=str)
            
            # Check if file exists and compare content
            if github_client.file_exists(file_path, branch_name):
                try:
                    existing_content = github_client.get_file(file_path, branch_name)
                    # Normalize both JSONs for comparison (parse and re-serialize)
                    existing_flow = json.loads(existing_content)
                    # Compare normalized JSON objects
                    if json.dumps(existing_flow, sort_keys=True, default=str) == json.dumps(flow, sort_keys=True, default=str):
                        skipped_count += 1
                        console.print(f"[yellow]⏭[/yellow] Skipped (unchanged): {flow_name}")
                        continue
                except Exception:
                    # If we can't read or compare, proceed with push
                    pass
            
            # Create commit message
            commit_message = message or f"Push flow: {flow_name}"
            
            # Push to GitHub
            github_client.create_or_update_file(file_path, flow_json, commit_message, branch_name)
            pushed_count += 1
            console.print(f"[green]✓[/green] Pushed: {flow_name}")
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


@git.command("pull")
@click.argument("flow_path", metavar="FLOW_PATH")
@click.option("--remote", help="Remote name (overrides current selection)")
@click.option("--branch", help="Branch name (overrides current selection)")
@click.option("--project-id", help="Project ID to associate the flow with")
@click.option("--project-name", help="Project name to associate the flow with")
@click.option("--profile", help="Profile to use (overrides default)")
@click.option("--ignore-version-check", is_flag=True, help="Ignore version mismatch warning")
def pull(
    flow_path: str,
    remote: Optional[str],
    branch: Optional[str],
    project_id: Optional[str],
    project_name: Optional[str],
    profile: Optional[str],
    ignore_version_check: bool
):
    """Pull a flow from GitHub repository to Langflow.
    
    FLOW_PATH must be a full path (e.g., 'ProjectName/FlowName_id.json'), not just a filename.
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
        
        # Initialize GitHub client
        github_client = GitHubClient(remote_name)
        
        # Validate that flow_path is a full path (must contain a slash)
        if "/" not in flow_path:
            raise ValueError(
                f"Flow path must be a full path (e.g., 'ProjectName/FlowName_id.json'), "
                f"not just a filename. Got: {flow_path}"
            )
        
        file_path = flow_path
        
        # Get file from GitHub
        console.print(f"[cyan]Pulling flow from {remote_name}/{branch_name}...[/cyan]")
        flow_json = github_client.get_file(file_path, branch_name)
        flow_data = json.loads(flow_json)
        
        # Get Langflow client
        langflow_client = LangflowAPIClient(profile_name=profile_name)
        
        # Resolve project
        resolved_project_id = resolve_project_id(project_id, project_name, langflow_client)
        
        # If resolved_project_id is None, try to infer from file path or flow_data
        if not resolved_project_id:
            projects_list = langflow_client.list_projects()
            # Try to infer from file path (project folder name)
            path_parts = file_path.split("/")
            if len(path_parts) > 1:
                project_folder = path_parts[0]
                # Try to find project by matching sanitized name
                for project in projects_list:
                    sanitized = GitHubClient.sanitize_name(project.get("name", ""))
                    if sanitized == project_folder:
                        resolved_project_id = project.get("id", project.get("project_id"))
                        break
        
        # If still no project, use the one from flow_data
        if not resolved_project_id:
            resolved_project_id = flow_data.get("folder_id") or flow_data.get("project_id")
        
        # Check if project exists, if not, try to create it from project.json
        if resolved_project_id:
            projects_list = langflow_client.list_projects()
            project_ids = [str(p.get("id", p.get("project_id", ""))) for p in projects_list]
            if str(resolved_project_id) not in project_ids:
                # Project doesn't exist, try to create it from project.json
                console.print(f"[yellow]Project {resolved_project_id} not found. Attempting to create from project.json...[/yellow]")
                
                # Extract project folder from path
                path_parts = file_path.split("/")
                if len(path_parts) > 1:
                    project_folder = path_parts[0]
                    project_json_path = f"{project_folder}/project.json"
                    
                    try:
                        # Try to get project.json from the repo
                        project_json_content = github_client.get_file(project_json_path, branch_name)
                        project_data = json.loads(project_json_content)
                        
                        # Remove flows attribute if present (we don't want to include flows when creating)
                        project_data.pop("flows", None)
                        # Remove id/project_id as the API will assign a new one
                        project_data.pop("id", None)
                        project_data.pop("project_id", None)
                        
                        # Get project name (required for creation)
                        project_name = project_data.get("name")
                        if not project_name:
                            raise ValueError("Project name not found in project.json")
                        
                        # Create the project
                        console.print(f"[cyan]Creating project '{project_name}' from project.json...[/cyan]")
                        created_project = langflow_client.create_project(project_name, project_data)
                        resolved_project_id = created_project.get("id", created_project.get("project_id"))
                        console.print(f"[green]✓[/green] Project '{project_name}' created successfully")
                        
                        # Refresh projects list
                        projects_list = langflow_client.list_projects()
                    except Exception as e:
                        console.print(f"[yellow]Warning: Could not create project from project.json: {str(e)}[/yellow]")
                        console.print(f"[yellow]Flow will be created without project association.[/yellow]")
                        resolved_project_id = None
                else:
                    console.print(f"[yellow]Warning: Could not determine project folder from path. Flow will be created without project association.[/yellow]")
                    resolved_project_id = None
        
        # Update flow_data with resolved project
        if resolved_project_id:
            flow_data["folder_id"] = resolved_project_id
        
        # Check if flow already exists (by ID)
        flow_id = flow_data.get("id") or flow_data.get("flow_id")
        flow_name = flow_data.get("name", "Unnamed")
        
        # Check version compatibility
        if "last_tested_version" in flow_data and not ignore_version_check:
            version_info = langflow_client.get_version()
            current_version = version_info.get("version")
            last_tested = flow_data.get("last_tested_version")
            
            if current_version and last_tested:
                current_version_str = str(current_version).strip()
                last_tested_str = str(last_tested).strip()
                
                if current_version_str != last_tested_str:
                    console.print(
                        f"\n[yellow]⚠[/yellow]  Version mismatch detected:\n"
                        f"  Flow was tested with version: [cyan]{last_tested_str}[/cyan]\n"
                        f"  Current environment version: [cyan]{current_version_str}[/cyan]\n"
                        f"  Use [bold]--ignore-version-check[/bold] to proceed anyway.\n"
                    )
                    if not click.confirm("Continue with flow pull?"):
                        console.print("[yellow]Flow pull cancelled.[/yellow]")
                        raise click.Abort()
        
        # Create or update flow
        if flow_id:
            try:
                # Try to get existing flow
                existing_flow = langflow_client.get_flow(flow_id)
                # Update existing flow
                result = langflow_client.update_flow(flow_id, flow_data)
                console.print(f"[green]✓[/green] Flow updated successfully")
            except Exception:
                # Flow doesn't exist, create new one
                result = langflow_client.create_flow(flow_name, flow_data)
                console.print(f"[green]✓[/green] Flow created successfully")
        else:
            # No ID, create new flow
            result = langflow_client.create_flow(flow_name, flow_data)
            console.print(f"[green]✓[/green] Flow created successfully")
        
        # Display result
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
        
    except ValueError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to pull flow: {str(e)}")
        raise click.Abort()

