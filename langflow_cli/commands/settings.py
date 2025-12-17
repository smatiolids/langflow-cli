"""Settings commands."""

import click
from rich.console import Console
from langflow_cli.api_client import LangflowAPIClient
from langflow_cli.utils import print_json


console = Console()


@click.group()
def settings():
    """Manage Langflow settings."""
    pass


@settings.command()
@click.option("--profile", help="Profile to use (overrides default)")
def get(profile: str):
    """Get current configuration."""
    try:
        client = LangflowAPIClient(profile_name=profile if profile else None)
        config = client.get_config()
        print_json(config, console)
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to get configuration: {str(e)}")
        raise click.Abort()

