"""Shared pytest fixtures and utilities for testing."""

import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from langflow_cli.cli import cli


@pytest.fixture
def runner():
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    """Mock the config directory to use a temporary path."""
    config_dir = tmp_path / ".langflow-cli"
    config_dir.mkdir()
    
    # Patch the get_config_dir function to return our temp directory
    from langflow_cli import config
    original_get_config_dir = config.get_config_dir
    
    def mock_get_config_dir():
        return config_dir
    
    monkeypatch.setattr(config, "get_config_dir", mock_get_config_dir)
    
    return config_dir


@pytest.fixture
def mock_profiles():
    """Create mock profile data for testing."""
    return {
        "profile1": {
            "url": "http://localhost:7860",
            "api_key": "test-api-key-1",
            "is_default": True,
        },
        "profile2": {
            "url": "http://localhost:7861",
            "api_key": "test-api-key-2",
            "is_default": False,
        },
    }


@pytest.fixture
def mock_api_client():
    """Create a mock LangflowAPIClient."""
    client = MagicMock()
    client.get_version.return_value = {
        "version": "1.0.0",
        "build": "12345",
    }
    return client

