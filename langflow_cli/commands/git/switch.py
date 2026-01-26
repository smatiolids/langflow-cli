"""Switch command for branch switching with optional creation."""

import click
from typing import Optional
from rich.console import Console
from langflow_cli.git_config import (
    get_current_remote,
    set_current_branch,
)
from langflow_cli.git_client import GitHubClient
from langflow_cli.config import get_default_profile

console = Console()


def register_switch_command(git_group: click.Group) -> None:
    """Register switch command with the git group."""
    
    @git_group.command("switch")
    @click.argument("branch_name")
    @click.option("--create", "-c", is_flag=True, help="Create branch if it doesn't exist")
    @click.option("--from-branch", help="Source branch when creating new branch (only used with --create)")
    @click.option("--remote", help="Remote name (overrides current selection)")
    @click.option("--profile", help="Profile to use (overrides default)")
    def switch(
        branch_name: str,
        create: bool,
        from_branch: Optional[str],
        remote: Optional[str],
        profile: Optional[str]
    ):
        """Switch to a branch, optionally creating it if it doesn't exist."""
        try:
            profile_name = profile or get_default_profile()
            if not profile_name:
                raise ValueError("No profile selected. Use 'langflow-cli env register' to create one.")
            
            remote_name = remote or get_current_remote(profile_name)
            if not remote_name:
                raise ValueError("No remote selected. Use 'langflow-cli git remote select <name>' first.")
            
            client = GitHubClient(remote_name)
            branches = client.get_branches()
            
            # Check if branch exists
            if branch_name not in branches:
                if create:
                    # Create branch from source
                    source_branch = from_branch or client.repo.default_branch
                    console.print(f"[cyan]Creating branch '{branch_name}' from '{source_branch}'...[/cyan]")
                    client.create_branch(branch_name, source_branch)
                    console.print(f"[green]✓[/green] Branch '{branch_name}' created")
                else:
                    console.print(f"[red]✗[/red] Branch '{branch_name}' not found")
                    console.print(f"[yellow]Available branches: {', '.join(branches)}[/yellow]")
                    console.print(f"[yellow]Use --create to create the branch[/yellow]")
                    raise click.Abort()
            
            # Switch to branch
            set_current_branch(profile_name, branch_name)
            console.print(f"[green]✓[/green] Switched to branch '{branch_name}'")
        except ValueError as e:
            console.print(f"[red]✗[/red] {str(e)}")
            raise click.Abort()
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to switch branch: {str(e)}")
            raise click.Abort()
