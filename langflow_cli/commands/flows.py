"""Flow management commands."""

import json
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from langflow_cli.api_client import LangflowAPIClient
from langflow_cli.utils import print_json, resolve_project_id, validate_project_id
from langflow_cli.flow_checks import validate_flow_with_checks, FlowCheck


console = Console()


@click.group()
def flows():
    """Manage Langflow flows."""
    pass


@flows.command()
@click.option("--project-id", help="Filter flows by project ID")
@click.option("--project-name", help="Filter flows by project name")
@click.option("--profile", help="Profile to use (overrides default)")
def list(project_id: str, project_name: str, profile: str):
    """List all flows, optionally filtered by project ID or project name."""
    try:
        client = LangflowAPIClient(profile_name=profile if profile else None)
        
        # Resolve project ID if project-name is provided
        if project_name and project_id:
            console.print("[yellow]Warning: Both --project-id and --project-name specified. Using --project-name.[/yellow]")
        
        resolved_project_id = resolve_project_id(project_id, project_name, client)
        flows_list = client.list_flows(project_id=resolved_project_id)
        
        if not flows_list:
            console.print("[yellow]No flows found.[/yellow]")
            return
        
        table = Table(title="Flows")
        table.add_column("Project ID", style="green")
        table.add_column("Project Name", style="green")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        
        for flow in flows_list:
            flow_id = flow.get("id", flow.get("flow_id", "N/A"))
            flow_name = flow.get("name", "Unnamed")
            project_id = flow.get("project_id", "N/A")
            project_name = flow.get("project_name", "N/A")
            
            table.add_row(
                str(project_id),
                project_name,
                str(flow_id),
                flow_name
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to list flows: {str(e)}")
        raise click.Abort()


@flows.command()
@click.argument("flow_id")
@click.option("--profile", help="Profile to use (overrides default)")
def get(flow_id: str, profile: str):
    """Get flow details by ID."""
    try:
        client = LangflowAPIClient(profile_name=profile if profile else None)
        flow = client.get_flow(flow_id)
        print_json(flow, console)
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to get flow: {str(e)}")
        raise click.Abort()


@flows.command()
@click.option("--name", help="Flow name")
@click.option("--data", help="Additional flow data as JSON string")
@click.option("--file", type=click.Path(exists=True, path_type=Path), help="Path to JSON file containing flow data")
@click.option("--project-id", help="Project ID to associate the flow with")
@click.option("--project-name", help="Project name to associate the flow with")
@click.option("--profile", help="Profile to use (overrides default)")
@click.option("--ignore-version-check", is_flag=True, help="Ignore version mismatch warning")
def create(name: str, data: str, file: Path, project_id: str, project_name: str, profile: str, ignore_version_check: bool):
    """Create a new flow."""
    try:
        client = LangflowAPIClient(profile_name=profile if profile else None)
        
        flow_data = {}
        
        # If file is provided, use its content (takes precedence over --data)
        if file:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    flow_data = json.load(f)
            except json.JSONDecodeError:
                console.print(f"[red]✗[/red] Invalid JSON in file: {file}")
                raise click.Abort()
            except IOError as e:
                console.print(f"[red]✗[/red] Failed to read file {file}: {str(e)}")
                raise click.Abort()
        elif data:
            flow_data = json.loads(data)

        if name:
            flow_data["name"] = name

        # Handle project-id and project-name parameters (command-line takes precedence)
        resolved_project_id = resolve_project_id(project_id, project_name, client)
        
        if resolved_project_id:
            # Validate project-id
            if not validate_project_id(resolved_project_id, client):
                raise ValueError(f"Project not found: {resolved_project_id}")
        
        # If no command-line project specified, check flow_data
        if not resolved_project_id:
            resolved_project_id = flow_data.get("folder_id") or flow_data.get("project_id")
        
        # Validate project exists if project_id is provided (from flow_data or resolved)
        if resolved_project_id:
            if not validate_project_id(resolved_project_id, client):
                raise ValueError(f"Project not found: {resolved_project_id}")
            # Add to flow_data as folder_id
            flow_data["folder_id"] = resolved_project_id
        
        # Run flow validation checks
        validate_flow_with_checks(
            flow_data,
            client,
            checks=[FlowCheck.LAST_TESTED_VERSION],  # Run all checks
            ignore_failures=ignore_version_check,
            console=console
        )
        
        flow = client.create_flow(name, flow_data)
        console.print(f"[green]✓[/green] Flow created successfully")
        
        # Extract only the requested attributes
        flow_id = flow.get("id", flow.get("flow_id", "N/A"))
        flow_name = flow.get("name", "N/A")
        flow_description = flow.get("description", "N/A")
        folder_id = flow.get("folder_id", flow.get("project_id", "N/A"))
        
        # Get project name
        projects_list = client.list_projects()
        project_name = "N/A"
        if folder_id and folder_id != "N/A":
            project = next(
                (p for p in projects_list if p.get("id", p.get("project_id")) == folder_id),
                None
            )
            if project:
                project_name = project.get("name", "N/A")
        
        # Create filtered response with only requested fields
        filtered_flow = {
            "id": flow_id,
            "name": flow_name,
            "description": flow_description,
            "project_id": folder_id,
            "project_name": project_name
        }
        
        print_json(filtered_flow, console)
    except json.JSONDecodeError:
        console.print(f"[red]✗[/red] Invalid JSON in --data option")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create flow: {str(e)}")
        raise click.Abort()


@flows.command()
@click.argument("flow_id")
@click.option("--data", required=True, help="Flow data as JSON string")
@click.option("--profile", help="Profile to use (overrides default)")
def update(flow_id: str, data: str, profile: str):
    """Update an existing flow."""
    try:
        client = LangflowAPIClient(profile_name=profile if profile else None)
        
        flow_data = json.loads(data)
        flow = client.update_flow(flow_id, flow_data)
        console.print(f"[green]✓[/green] Flow updated successfully")
        print_json(flow, console)
    except json.JSONDecodeError:
        console.print(f"[red]✗[/red] Invalid JSON in --data option")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to update flow: {str(e)}")
        raise click.Abort()


@flows.command()
@click.argument("flow_id")
@click.option("--profile", help="Profile to use (overrides default)")
@click.confirmation_option(prompt="Are you sure you want to delete this flow?")
def delete(flow_id: str, profile: str):
    """Delete a flow."""
    try:
        client = LangflowAPIClient(profile_name=profile if profile else None)
        client.delete_flow(flow_id)
        console.print(f"[green]✓[/green] Flow '{flow_id}' deleted successfully")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to delete flow: {str(e)}")
        raise click.Abort()

