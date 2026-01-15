"""Main CLI entry point for Langflow CLI."""

import sys
import click
from rich.console import Console
from langflow_cli.commands import env as env_commands
from langflow_cli.commands import settings as settings_commands
from langflow_cli.commands import flows as flows_commands
from langflow_cli.commands import projects as projects_commands
from langflow_cli.commands import git as git_commands
from langflow_cli.commands import status as status_command
from langflow_cli.utils import print_banner

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Langflow CLI - Manage Langflow environments and resources."""
    # Show banner when no subcommand is provided
    if ctx.invoked_subcommand is None:
        print_banner(console)
        # Show help after banner
        click.echo(ctx.get_help())
        sys.exit(0)


# Register command groups
cli.add_command(env_commands.env, name="env")
cli.add_command(settings_commands.settings, name="settings")
cli.add_command(flows_commands.flows, name="flows")
cli.add_command(projects_commands.projects, name="projects")
cli.add_command(git_commands.git, name="git")
cli.add_command(status_command.status, name="status")


def main():
    """Entry point for the langflow-cli command."""
    cli()

