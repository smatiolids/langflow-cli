"""Utility functions for Langflow CLI."""

import json
from typing import Any, Optional, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from langflow_cli.api_client import LangflowAPIClient

from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

def print_json(data: Any, console: Optional[Console] = None) -> None:
    """
    Pretty print JSON data with colors.
    
    Args:
        data: Data to print (will be converted to JSON)
        console: Rich console instance (creates new one if not provided)
    """
    if console is None:
        console = Console()
    
    json_str = json.dumps(data, indent=2, default=str)
    console.print(JSON(json_str))


def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
    """
    Mask an API key, showing only the first few characters.
    
    Args:
        api_key: The API key to mask
        visible_chars: Number of characters to show at the start
        
    Returns:
        Masked API key string
    """
    if len(api_key) <= visible_chars:
        return "*" * len(api_key)
    return api_key[:visible_chars] + "*" * (len(api_key) - visible_chars)


def resolve_project_id(
    project_id: Optional[str],
    project_name: Optional[str],
    client: "LangflowAPIClient"
) -> Optional[str]:
    """
    Resolve project ID from either project_id or project_name.
    
    Args:
        project_id: Project ID (if provided, returned directly)
        project_name: Project name (if provided, will be resolved to ID)
        client: LangflowAPIClient instance to call list_projects()
        
    Returns:
        Project ID as string, or None if neither parameter is provided
        
    Raises:
        ValueError: If project_name is provided but project is not found
    """
    # If project_id is provided, return it directly
    if project_id:
        return project_id
    
    # If project_name is provided, resolve it to project_id
    if project_name:
        projects_list = client.list_projects()
        matching_project = next(
            (p for p in projects_list if p.get("name") == project_name),
            None
        )
        if not matching_project:
            raise ValueError(f"Project not found: {project_name}")
        return matching_project.get("id", matching_project.get("project_id"))
    
    # Neither provided, return None
    return None


def validate_project_id(project_id: str, client: "LangflowAPIClient") -> bool:
    """
    Check if a project ID exists.
    
    Args:
        project_id: Project ID to validate
        client: LangflowAPIClient instance to call list_projects()
        
    Returns:
        True if project exists, False otherwise
    """
    if not project_id:
        return False
    projects_list = client.list_projects()
    project_ids = [
        str(p.get("id", p.get("project_id", ""))) 
        for p in projects_list
    ]
    return str(project_id) in project_ids


def print_banner(console: Optional[Console] = None) -> None:
    """
    Print the Langflow CLI banner.
    
    Args:
        console: Rich console instance (creates new one if not provided)
    """
    if console is None:
        console = Console()
    
    try:
        from langflow_cli import __version__
        version_text = f"v{__version__}"
    except ImportError:
        version_text = ""
    

    logo = Text(
        """

██╗      ███████╗      ██████╗██╗     ██╗
██║      ██╔════╝     ██╔════╝██║     ██║
██║      █████╗   ██  ██║     ██║     ██║
██║      ██╔══╝       ██║     ██║     ██║
███████╗ ██║          ╚██████╗███████╗██║
╚══════╝ ╚═╝           ╚═════╝╚══════╝╚═╝

"""+f"Langflow CLI {version_text}",
        style="bold purple",
        justify="left",
    )

    console.print(logo)
    console.print()

