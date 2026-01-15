"""Status command to show current environment and Git configuration."""

import click
from rich.console import Console
from rich.table import Table
from langflow_cli.config import get_default_profile, load_profile
from langflow_cli.git_config import get_current_selection, get_remote
from langflow_cli.utils import mask_api_key, print_banner


console = Console()


@click.command()
@click.option("--profile", help="Profile to check (overrides default)")
def status(profile: str):
    """Show current environment and Git configuration."""
    print_banner(console)
    try:
        # Get current profile
        profile_name = profile if profile else get_default_profile()
        
        if profile_name is None:
            console.print("[yellow]No default profile set. Use 'langflow-cli env register' to create one.[/yellow]")
            profile_url = None
            api_key = None
        else:
            profile_url, api_key = load_profile(profile_name)
        
        # Get Git configuration
        git_remote = None
        git_branch = None
        git_remote_url = None
        
        if profile_name:
            try:
                git_remote, git_branch = get_current_selection(profile_name)
                # Get remote URL if remote is set
                if git_remote:
                    try:
                        remote_config = get_remote(git_remote)
                        git_remote_url = remote_config.get("url")
                    except Exception:
                        git_remote_url = None
            except Exception:
                pass
        
        # Create and display status table
        table = Table(title="Current Status", show_header=True, header_style="bold")
        table.add_column("Category", style="cyan")
        table.add_column("Value", style="green")
        
        # Environment information
        table.add_row("Environment", profile_name or "N/A")
        table.add_row("URL", profile_url or "N/A")
        if api_key:
            table.add_row("API Key", mask_api_key(api_key))
        
        # Git information
        table.add_row("", "")  # Empty row for separation
        table.add_row("Git Remote", git_remote or "N/A")
        if git_remote_url:
            table.add_row("Git Remote URL", git_remote_url)
        table.add_row("Git Branch", git_branch or "N/A")
        
        console.print("\n")
        console.print(table)
        console.print("")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to get status: {str(e)}")
        raise click.Abort()

