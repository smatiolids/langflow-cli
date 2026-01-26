"""Remote management commands."""

import click
from typing import Optional
from rich.console import Console
from rich.table import Table
from langflow_cli.git_config import (
    add_remote,
    list_remotes,
    remove_remote,
    update_remote_token,
    set_current_remote,
    set_current_branch,
    get_current_remote,
    get_current_branch,
    get_remote,
)
from langflow_cli.git_client import GitHubClient
from langflow_cli.config import get_default_profile

console = Console()


def register_remote_commands(git_group: click.Group) -> None:
    """Register remote management commands with the git group."""
    
    @git_group.group()
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

    @remote.command("set-token")
    @click.argument("name")
    @click.option("--token", required=True, help="GitHub personal access token (required)")
    def remote_set_token(name: str, token: str):
        """Update the personal access token for a remote."""
        try:
            update_remote_token(name, token)
            console.print(f"[green]✓[/green] Token updated for remote '{name}'")
        except ValueError as e:
            console.print(f"[red]✗[/red] {str(e)}")
            raise click.Abort()
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to update token: {str(e)}")
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
            get_remote(name)
            
            set_current_remote(profile_name, name)
            console.print(f"[green]✓[/green] Remote '{name}' selected for profile '{profile_name}'")
            
            # If branch is provided, verify it exists and set it
            if branch:
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
