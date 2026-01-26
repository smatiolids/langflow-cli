"""Branch management commands."""

import click
from typing import Optional
from rich.console import Console
from rich.table import Table
from langflow_cli.git_config import (
    get_current_remote,
    get_current_branch,
    set_current_branch,
)
from langflow_cli.git_client import GitHubClient
from langflow_cli.config import get_default_profile

console = Console()


def register_branch_command(git_group: click.Group) -> None:
    """Register branch command with the git group."""
    
    @git_group.command("branch")
    @click.argument("action", type=click.Choice(["list", "create", "delete"]))
    @click.argument("branch_name", required=False)
    @click.option("--from-branch", "--source-branch", help="Source branch to create from (defaults to default branch)")
    @click.option("--force", is_flag=True, help="Skip confirmation prompt (for delete)")
    @click.option("--remote", help="Remote name (overrides current selection)")
    @click.option("--profile", help="Profile to use (overrides default)")
    def branch(
        action: str,
        branch_name: Optional[str],
        from_branch: Optional[str],
        force: bool,
        remote: Optional[str],
        profile: Optional[str]
    ):
        """Manage branches: list, create, or delete."""
        try:
            profile_name = profile or get_default_profile()
            if not profile_name:
                raise ValueError("No profile selected. Use 'langflow-cli env register' to create one.")
            
            remote_name = remote or get_current_remote(profile_name)
            if not remote_name:
                raise ValueError("No remote selected. Use 'langflow-cli git remote select <name>' first.")
            
            client = GitHubClient(remote_name)
            
            if action == "list":
                _branch_list(client, remote_name, profile_name)
            elif action == "create":
                if not branch_name:
                    raise ValueError("Branch name is required for create action")
                _branch_create(client, branch_name, from_branch, remote_name, profile_name)
            elif action == "delete":
                if not branch_name:
                    raise ValueError("Branch name is required for delete action")
                _branch_delete(client, branch_name, force, remote_name, profile_name)
        except ValueError as e:
            console.print(f"[red]✗[/red] {str(e)}")
            raise click.Abort()
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to {action} branch: {str(e)}")
            raise click.Abort()


def _branch_list(client: GitHubClient, remote_name: str, profile_name: str) -> None:
    """List available branches."""
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


def _branch_create(
    client: GitHubClient,
    branch_name: str,
    from_branch: Optional[str],
    remote_name: str,
    profile_name: str
) -> None:
    """Create a new branch."""
    # Check if branch already exists
    branches = client.get_branches()
    if branch_name in branches:
        raise ValueError(f"Branch '{branch_name}' already exists")
    
    # Determine source branch
    source_branch = from_branch or client.repo.default_branch
    
    # Verify source branch exists
    if source_branch not in branches:
        raise ValueError(f"Source branch '{source_branch}' not found")
    
    # Create branch
    console.print(f"[cyan]Creating branch '{branch_name}' from '{source_branch}'...[/cyan]")
    client.create_branch(branch_name, source_branch)
    console.print(f"[green]✓[/green] Branch '{branch_name}' created successfully")
    
    # Optionally set as current branch
    current_branch = get_current_branch(profile_name)
    if not current_branch:
        set_current_branch(profile_name, branch_name)
        console.print(f"[green]✓[/green] Switched to branch '{branch_name}'")


def _branch_delete(
    client: GitHubClient,
    branch_name: str,
    force: bool,
    remote_name: str,
    profile_name: str
) -> None:
    """Delete a branch."""
    # Check if branch exists
    branches = client.get_branches()
    if branch_name not in branches:
        raise ValueError(f"Branch '{branch_name}' not found")
    
    # Prevent deletion of default branch
    if branch_name == client.repo.default_branch:
        raise ValueError(f"Cannot delete default branch '{branch_name}'")
    
    # Warn if deleting current branch
    current_branch = get_current_branch(profile_name)
    if branch_name == current_branch:
        console.print(f"[yellow]⚠[/yellow]  You are about to delete the current branch '{branch_name}'")
        if not force and not click.confirm("Continue?"):
            raise click.Abort()
    
    # Confirm deletion unless force is used
    if not force:
        if not click.confirm(f"Delete branch '{branch_name}'?"):
            raise click.Abort()
    
    # Delete branch
    console.print(f"[cyan]Deleting branch '{branch_name}'...[/cyan]")
    client.delete_branch(branch_name)
    console.print(f"[green]✓[/green] Branch '{branch_name}' deleted successfully")
    
    # If it was the current branch, clear it
    if branch_name == current_branch:
        # Note: We don't have a clear_current_branch function, so we'll just inform the user
        console.print(f"[yellow]Note: Branch '{branch_name}' was your current branch. Use 'langflow-cli git checkout <branch>' to select a new branch.[/yellow]")
