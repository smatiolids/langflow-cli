"""Checkout command."""

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


def register_checkout_command(git_group: click.Group) -> None:
    """Register checkout command with the git group."""
    
    @git_group.command("checkout")
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
