"""Flow management commands."""

import json
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from langflow_cli.api_client import LangflowAPIClient
from langflow_cli.utils import print_json


console = Console()


@click.group()
def flows():
    """Manage Langflow flows."""
    pass


@flows.command()
@click.option("--profile", help="Profile to use (overrides default)")
def list(profile: str):
    """List all flows."""
    try:
        client = LangflowAPIClient(profile_name=profile if profile else None)
        flows_list = client.list_flows()
        projects_list = client.list_projects()
        
        if not flows_list:
            console.print("[yellow]No flows found.[/yellow]")
            return
        
        # Enrich flows with project information and sort by project name
        enriched_flows = []
        for flow in flows_list:
            flow_id = flow.get("id", flow.get("flow_id", "N/A"))
            flow_name = flow.get("name", "Unnamed")
            project_id = flow.get("folder_id", flow.get("project_id", "N/A"))
            project_name = next((p['name'] for p in projects_list if p['id'] == project_id), "N/A")
            
            enriched_flows.append({
                'flow_id': flow_id,
                'flow_name': flow_name,
                'project_id': project_id,
                'project_name': project_name,
                'flow_data': flow  # Keep original flow data
            })
        
        # Sort by project name (case-insensitive)
        enriched_flows.sort(key=lambda x: x['project_name'].lower() if x['project_name'] != "N/A" else "zzz")
        
        table = Table(title="Flows")
        table.add_column("Project ID", style="green")
        table.add_column("Project Name", style="green")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        
        for enriched_flow in enriched_flows:
            table.add_row(
                str(enriched_flow['project_id']),
                enriched_flow['project_name'],
                str(enriched_flow['flow_id']),
                enriched_flow['flow_name']
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
def create(name: str, data: str, file: Path, project_id: str, project_name: str, profile: str):
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

        projects_list = client.list_projects()
        
        # Helper function to validate project ID exists
        def validate_project_id(pid: str) -> bool:
            """Check if a project ID exists in the projects list."""
            if not pid:
                return False
            project_ids = [
                str(p.get("id", p.get("project_id", ""))) 
                for p in projects_list
            ]
            return str(pid) in project_ids
        
        # Handle project-id and project-name parameters (command-line takes precedence)
        resolved_project_id = None
        
        if project_id:
            # Validate project-id immediately
            if not validate_project_id(project_id):
                raise ValueError(f"Project not found: {project_id}")
            resolved_project_id = project_id
        elif project_name:
            # Find project by name
            matching_project = next(
                (p for p in projects_list if p.get("name") == project_name),
                None
            )
            if not matching_project:
                raise ValueError(f"Project not found: {project_name}")
            resolved_project_id = matching_project.get("id", matching_project.get("project_id"))
        
        # If no command-line project specified, check flow_data
        if not resolved_project_id:
            resolved_project_id = flow_data.get("folder_id") or flow_data.get("project_id")
        
        # Validate project exists if project_id is provided (from flow_data or resolved)
        if resolved_project_id:
            if not validate_project_id(resolved_project_id):
                raise ValueError(f"Project not found: {resolved_project_id}")
            # Add to flow_data as folder_id
            flow_data["folder_id"] = resolved_project_id
        
        flow = client.create_flow(name, flow_data)
        console.print(f"[green]✓[/green] Flow created successfully")
        print_json(flow, console)
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

