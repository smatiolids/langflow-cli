"""Utility functions for Langflow CLI."""

import json
from typing import Any, Optional
from rich.console import Console
from rich.json import JSON


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

