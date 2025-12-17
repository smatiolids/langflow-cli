"""Configuration management for Langflow CLI using AWS CLI-style approach."""

import configparser
import os
from pathlib import Path
from typing import Optional, Dict, Tuple


def get_config_dir() -> Path:
    """Returns the path to the ~/.langflow-cli directory."""
    return Path.home() / ".langflow-cli"


def get_config_path() -> Path:
    """Returns the path to the config file."""
    return get_config_dir() / "config"


def get_credentials_path() -> Path:
    """Returns the path to the credentials file."""
    return get_config_dir() / "credentials"


def _ensure_config_dir() -> None:
    """Create the config directory if it doesn't exist."""
    config_dir = get_config_dir()
    config_dir.mkdir(mode=0o700, exist_ok=True)


def _ensure_config_file() -> None:
    """Create the config file if it doesn't exist."""
    _ensure_config_dir()
    config_path = get_config_path()
    if not config_path.exists():
        config_path.touch(mode=0o644)
        # Initialize with default section
        config = configparser.ConfigParser()
        config.add_section("default")
        with open(config_path, "w") as f:
            config.write(f)


def _ensure_credentials_file() -> None:
    """Create the credentials file if it doesn't exist."""
    _ensure_config_dir()
    creds_path = get_credentials_path()
    if not creds_path.exists():
        creds_path.touch(mode=0o600)
        # Initialize with empty file
        config = configparser.ConfigParser()
        with open(creds_path, "w") as f:
            config.write(f)


def load_profile(profile_name: Optional[str] = None) -> Tuple[str, str]:
    """
    Load profile configuration and credentials.
    
    Args:
        profile_name: Name of the profile to load. If None, loads default profile.
        
    Returns:
        Tuple of (url, api_key)
        
    Raises:
        ValueError: If profile doesn't exist or is not configured.
    """
    if profile_name is None:
        profile_name = get_default_profile()
        if profile_name is None:
            raise ValueError("No default profile set. Use 'langflow-cli env register' to create one.")
    
    _ensure_config_file()
    _ensure_credentials_file()
    
    config = configparser.ConfigParser()
    config.read(get_config_path())
    
    creds = configparser.ConfigParser()
    creds.read(get_credentials_path())
    
    profile_section = f"profile {profile_name}"
    if not config.has_section(profile_section):
        raise ValueError(f"Profile '{profile_name}' not found in config file.")
    
    if not config.has_option(profile_section, "url"):
        raise ValueError(f"Profile '{profile_name}' is missing 'url' in config file.")
    
    url = config.get(profile_section, "url")
    
    if not creds.has_section(profile_name):
        raise ValueError(f"Profile '{profile_name}' not found in credentials file.")
    
    if not creds.has_option(profile_name, "api_key"):
        raise ValueError(f"Profile '{profile_name}' is missing 'api_key' in credentials file.")
    
    api_key = creds.get(profile_name, "api_key")
    
    return url, api_key


def save_profile(profile_name: str, url: str, api_key: str) -> None:
    """
    Save profile configuration and credentials.
    
    Args:
        profile_name: Name of the profile
        url: Langflow API URL
        api_key: API key for authentication
    """
    _ensure_config_file()
    _ensure_credentials_file()
    
    # Save to config file
    config = configparser.ConfigParser()
    config.read(get_config_path())
    
    profile_section = f"profile {profile_name}"
    if not config.has_section(profile_section):
        config.add_section(profile_section)
    
    config.set(profile_section, "url", url)
    
    # Set as default if it's the first profile
    if not config.has_option("default", "profile"):
        if not config.has_section("default"):
            config.add_section("default")
        config.set("default", "profile", profile_name)
    
    with open(get_config_path(), "w") as f:
        config.write(f)
    
    # Save to credentials file
    creds = configparser.ConfigParser()
    creds.read(get_credentials_path())
    
    if not creds.has_section(profile_name):
        creds.add_section(profile_name)
    
    creds.set(profile_name, "api_key", api_key)
    
    with open(get_credentials_path(), "w") as f:
        creds.write(f)
    
    # Set file permissions
    os.chmod(get_credentials_path(), 0o600)
    os.chmod(get_config_path(), 0o644)


def get_default_profile() -> Optional[str]:
    """
    Get the current default profile name.
    
    Returns:
        Default profile name, or None if not set.
    """
    _ensure_config_file()
    config = configparser.ConfigParser()
    config.read(get_config_path())
    
    if config.has_section("default") and config.has_option("default", "profile"):
        return config.get("default", "profile")
    
    return None


def set_default_profile(profile_name: str) -> None:
    """
    Set the default profile.
    
    Args:
        profile_name: Name of the profile to set as default
        
    Raises:
        ValueError: If profile doesn't exist.
    """
    _ensure_config_file()
    config = configparser.ConfigParser()
    config.read(get_config_path())
    
    profile_section = f"profile {profile_name}"
    if not config.has_section(profile_section):
        raise ValueError(f"Profile '{profile_name}' does not exist.")
    
    if not config.has_section("default"):
        config.add_section("default")
    
    config.set("default", "profile", profile_name)
    
    with open(get_config_path(), "w") as f:
        config.write(f)


def list_profiles() -> Dict[str, Dict[str, str]]:
    """
    List all registered profiles.
    
    Returns:
        Dictionary mapping profile names to their configuration (without API keys).
    """
    _ensure_config_file()
    config = configparser.ConfigParser()
    config.read(get_config_path())
    
    profiles = {}
    default_profile = get_default_profile()
    
    for section in config.sections():
        if section.startswith("profile "):
            profile_name = section[8:]  # Remove "profile " prefix
            url = config.get(section, "url") if config.has_option(section, "url") else None
            profiles[profile_name] = {
                "url": url,
                "is_default": profile_name == default_profile,
            }
    
    return profiles


def delete_profile(profile_name: str) -> None:
    """
    Delete a profile from both config and credentials files.
    
    Args:
        profile_name: Name of the profile to delete
        
    Raises:
        ValueError: If profile doesn't exist.
    """
    _ensure_config_file()
    _ensure_credentials_file()
    
    config = configparser.ConfigParser()
    config.read(get_config_path())
    
    creds = configparser.ConfigParser()
    creds.read(get_credentials_path())
    
    profile_section = f"profile {profile_name}"
    
    if not config.has_section(profile_section):
        raise ValueError(f"Profile '{profile_name}' does not exist.")
    
    # Remove from config
    config.remove_section(profile_section)
    
    # Remove from credentials
    if creds.has_section(profile_name):
        creds.remove_section(profile_name)
    
    # If this was the default profile, clear the default
    default_profile = get_default_profile()
    if default_profile == profile_name:
        if config.has_section("default"):
            config.remove_option("default", "profile")
    
    with open(get_config_path(), "w") as f:
        config.write(f)
    
    with open(get_credentials_path(), "w") as f:
        creds.write(f)

