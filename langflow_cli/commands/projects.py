"""Project management commands."""

import json
import click
from rich.console import Console
from rich.table import Table
from langflow_cli.api_client import LangflowAPIClient
from langflow_cli.utils import print_json


console = Console()


@click.group()
def projects():
    """Manage Langflow projects."""
    pass


@projects.command()
@click.option("--profile", help="Profile to use (overrides default)")
def list(profile: str):
    """List all projects."""
    try:
        client = LangflowAPIClient(profile_name=profile if profile else None)
        projects_list = client.list_projects()
        
        if not projects_list:
            console.print("[yellow]No projects found.[/yellow]")
            return
        
        table = Table(title="Projects")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        
        for project in projects_list:
            project_id = project.get("id", project.get("project_id", "N/A"))
            project_name = project.get("name", "Unnamed")
            table.add_row(str(project_id), project_name)
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to list projects: {str(e)}")
        raise click.Abort()


@projects.command()
@click.argument("project_id")
@click.option("--profile", help="Profile to use (overrides default)")
def get(project_id: str, profile: str):
    """Get project details by ID."""
    try:
        client = LangflowAPIClient(profile_name=profile if profile else None)
        project = client.get_project(project_id)
        print_json(project, console)
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to get project: {str(e)}")
        raise click.Abort()


@projects.command()
@click.option("--name", required=True, help="Project name")
@click.option("--data", help="Additional project data as JSON string")
@click.option("--profile", help="Profile to use (overrides default)")
def create(name: str, data: str, profile: str):
    """Create a new project."""
    try:
        client = LangflowAPIClient(profile_name=profile if profile else None)
        
        project_data = {}
        if data:
            project_data = json.loads(data)
        
        project = client.create_project(name, project_data)
        console.print(f"[green]✓[/green] Project created successfully")
        print_json(project, console)
    except json.JSONDecodeError:
        console.print(f"[red]✗[/red] Invalid JSON in --data option")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create project: {str(e)}")
        raise click.Abort()


@projects.command()
@click.argument("project_id")
@click.option("--data", required=True, help="Project data as JSON string")
@click.option("--profile", help="Profile to use (overrides default)")
def update(project_id: str, data: str, profile: str):
    """Update an existing project."""
    try:
        client = LangflowAPIClient(profile_name=profile if profile else None)
        
        project_data = json.loads(data)
        project = client.update_project(project_id, project_data)
        console.print(f"[green]✓[/green] Project updated successfully")
        print_json(project, console)
    except json.JSONDecodeError:
        console.print(f"[red]✗[/red] Invalid JSON in --data option")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to update project: {str(e)}")
        raise click.Abort()


@projects.command()
@click.argument("project_id")
@click.option("--profile", help="Profile to use (overrides default)")
@click.confirmation_option(prompt="Are you sure you want to delete this project?")
def delete(project_id: str, profile: str):
    """Delete a project."""
    try:
        client = LangflowAPIClient(profile_name=profile if profile else None)
        client.delete_project(project_id)
        console.print(f"[green]✓[/green] Project '{project_id}' deleted successfully")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to delete project: {str(e)}")
        raise click.Abort()

