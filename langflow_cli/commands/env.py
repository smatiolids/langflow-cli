"""Environment management commands."""

import click
from rich.console import Console
from rich.table import Table
from langflow_cli.config import (
    save_profile,
    list_profiles,
    set_default_profile,
    get_default_profile,
    load_profile,
    delete_profile,
)
from langflow_cli.utils import mask_api_key


console = Console()


@click.group()
def env():
    """Manage Langflow environments/profiles."""
    pass


@env.command()
@click.argument("name")
@click.option("--url", required=True, help="Langflow API URL")
@click.option("--api-key", required=True, help="API key for authentication")
def register(name: str, url: str, api_key: str):
    """Register a new environment/profile."""
    try:
        save_profile(name, url, api_key)
        console.print(f"[green]✓[/green] Profile '{name}' registered successfully")
        
        # Check if this is the first profile (now default)
        default = get_default_profile()
        if default == name:
            console.print(f"[green]✓[/green] Profile '{name}' set as default")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to register profile: {str(e)}")
        raise click.Abort()


@env.command()
def list():
    """List all registered environments/profiles."""
    try:
        profiles = list_profiles()
        
        if not profiles:
            console.print("[yellow]No profiles registered. Use 'langflow-cli env register' to create one.[/yellow]")
            return
        
        table = Table(title="Registered Profiles")
        table.add_column("Name", style="cyan")
        table.add_column("URL", style="magenta")
        table.add_column("Default", style="green")
        
        for profile_name, info in profiles.items():
            default_mark = "✓" if info["is_default"] else ""
            table.add_row(profile_name, info["url"], default_mark)
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to list profiles: {str(e)}")
        raise click.Abort()


@env.command()
@click.argument("name")
def select(name: str):
    """Select active/default environment."""
    try:
        set_default_profile(name)
        console.print(f"[green]✓[/green] Profile '{name}' set as default")
    except ValueError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to set default profile: {str(e)}")
        raise click.Abort()


@env.command()
def current():
    """Show current/default environment."""
    try:
        default_profile = get_default_profile()
        
        if default_profile is None:
            console.print("[yellow]No default profile set. Use 'langflow-cli env register' to create one.[/yellow]")
            return
        
        url, api_key = load_profile(default_profile)
        
        console.print(f"\n[bold]Current Profile:[/bold] {default_profile}")
        console.print(f"[bold]URL:[/bold] {url}")
        console.print(f"[bold]API Key:[/bold] {mask_api_key(api_key)}")
    except Exception as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()


@env.command()
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this profile?")
def delete(name: str):
    """Delete an environment/profile."""
    try:
        default_profile = get_default_profile()
        delete_profile(name)
        console.print(f"[green]✓[/green] Profile '{name}' deleted successfully")
        
        # If we deleted the default, inform the user
        if default_profile == name:
            new_default = get_default_profile()
            if new_default:
                console.print(f"[yellow]Default profile changed to '{new_default}'[/yellow]")
            else:
                console.print("[yellow]No default profile set. Use 'langflow-cli env select' to set one.[/yellow]")
    except ValueError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to delete profile: {str(e)}")
        raise click.Abort()

