"""Tests for environment management commands."""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from langflow_cli.cli import cli


class TestEnvRegister:
    """Tests for the 'env register' command."""
    
    def test_register_new_profile(self, runner, mock_config_dir):
        """Test registering a new profile."""
        with patch("langflow_cli.commands.env.save_profile") as mock_save, \
             patch("langflow_cli.commands.env.get_default_profile", return_value="test-profile") as mock_get_default:
            
            result = runner.invoke(
                cli,
                ["env", "register", "test-profile", "--url", "http://localhost:7860", "--api-key", "test-key"]
            )
            
            assert result.exit_code == 0
            mock_save.assert_called_once_with("test-profile", "http://localhost:7860", "test-key")
            assert "Profile 'test-profile' registered successfully" in result.output
            assert "Profile 'test-profile' set as default" in result.output
    
    def test_register_profile_missing_url(self, runner):
        """Test that register fails when URL is missing."""
        result = runner.invoke(
            cli,
            ["env", "register", "test-profile", "--api-key", "test-key"]
        )
        
        assert result.exit_code != 0
        assert "Missing option" in result.output or "Error" in result.output
    
    def test_register_profile_missing_api_key(self, runner):
        """Test that register fails when API key is missing."""
        result = runner.invoke(
            cli,
            ["env", "register", "test-profile", "--url", "http://localhost:7860"]
        )
        
        assert result.exit_code != 0
        assert "Missing option" in result.output or "Error" in result.output
    
    def test_register_profile_error_handling(self, runner):
        """Test error handling when profile registration fails."""
        with patch("langflow_cli.commands.env.save_profile", side_effect=Exception("Config error")):
            result = runner.invoke(
                cli,
                ["env", "register", "test-profile", "--url", "http://localhost:7860", "--api-key", "test-key"]
            )
            
            assert result.exit_code != 0
            assert "Failed to register profile" in result.output


class TestEnvList:
    """Tests for the 'env list' command."""
    
    def test_list_profiles_empty(self, runner):
        """Test listing profiles when none exist."""
        with patch("langflow_cli.commands.env.list_profiles", return_value={}):
            result = runner.invoke(cli, ["env", "list"])
            
            assert result.exit_code == 0
            assert "No profiles registered" in result.output
    
    def test_list_profiles_with_data(self, runner, mock_profiles):
        """Test listing profiles with existing data."""
        with patch("langflow_cli.commands.env.list_profiles", return_value={
            "profile1": {"url": "http://localhost:7860", "is_default": True},
            "profile2": {"url": "http://localhost:7861", "is_default": False},
        }):
            result = runner.invoke(cli, ["env", "list"])
            
            assert result.exit_code == 0
            assert "profile1" in result.output
            assert "profile2" in result.output
            assert "http://localhost:7860" in result.output
            assert "http://localhost:7861" in result.output
    
    def test_list_profiles_error_handling(self, runner):
        """Test error handling when listing profiles fails."""
        with patch("langflow_cli.commands.env.list_profiles", side_effect=Exception("Config error")):
            result = runner.invoke(cli, ["env", "list"])
            
            assert result.exit_code != 0
            assert "Failed to list profiles" in result.output


class TestEnvSelect:
    """Tests for the 'env select' command."""
    
    def test_select_existing_profile(self, runner):
        """Test selecting an existing profile as default."""
        with patch("langflow_cli.commands.env.set_default_profile") as mock_set:
            result = runner.invoke(cli, ["env", "select", "test-profile"])
            
            assert result.exit_code == 0
            mock_set.assert_called_once_with("test-profile")
            assert "Profile 'test-profile' set as default" in result.output
    
    def test_select_nonexistent_profile(self, runner):
        """Test selecting a profile that doesn't exist."""
        with patch("langflow_cli.commands.env.set_default_profile", side_effect=ValueError("Profile 'test-profile' does not exist.")):
            result = runner.invoke(cli, ["env", "select", "test-profile"])
            
            assert result.exit_code != 0
            assert "Profile 'test-profile' does not exist" in result.output
    
    def test_select_profile_error_handling(self, runner):
        """Test error handling when setting default profile fails."""
        with patch("langflow_cli.commands.env.set_default_profile", side_effect=Exception("Config error")):
            result = runner.invoke(cli, ["env", "select", "test-profile"])
            
            assert result.exit_code != 0
            assert "Failed to set default profile" in result.output


class TestEnvCurrent:
    """Tests for the 'env current' command."""
    
    def test_current_profile_exists(self, runner):
        """Test showing current profile when one exists."""
        with patch("langflow_cli.commands.env.get_default_profile", return_value="test-profile"), \
             patch("langflow_cli.commands.env.load_profile", return_value=("http://localhost:7860", "test-api-key-12345")), \
             patch("langflow_cli.commands.env.mask_api_key", return_value="test*****"):
            
            result = runner.invoke(cli, ["env", "current"])
            
            assert result.exit_code == 0
            assert "Current Profile: test-profile" in result.output
            assert "http://localhost:7860" in result.output
            assert "test*****" in result.output
    
    def test_current_profile_none(self, runner):
        """Test showing current profile when none is set."""
        with patch("langflow_cli.commands.env.get_default_profile", return_value=None):
            result = runner.invoke(cli, ["env", "current"])
            
            assert result.exit_code == 0
            assert "No default profile set" in result.output
    
    def test_current_profile_error_handling(self, runner):
        """Test error handling when getting current profile fails."""
        with patch("langflow_cli.commands.env.get_default_profile", side_effect=Exception("Config error")):
            result = runner.invoke(cli, ["env", "current"])
            
            assert result.exit_code != 0


class TestEnvDelete:
    """Tests for the 'env delete' command."""
    
    def test_delete_existing_profile(self, runner):
        """Test deleting an existing profile."""
        with patch("langflow_cli.commands.env.get_default_profile", return_value="other-profile"), \
             patch("langflow_cli.commands.env.delete_profile") as mock_delete:
            
            result = runner.invoke(
                cli,
                ["env", "delete", "test-profile"],
                input="y\n"  # Confirm deletion
            )
            
            assert result.exit_code == 0
            mock_delete.assert_called_once_with("test-profile")
            assert "Profile 'test-profile' deleted successfully" in result.output
    
    def test_delete_default_profile(self, runner):
        """Test deleting the default profile."""
        with patch("langflow_cli.commands.env.get_default_profile", side_effect=["test-profile", "other-profile"]), \
             patch("langflow_cli.commands.env.delete_profile") as mock_delete:
            
            result = runner.invoke(
                cli,
                ["env", "delete", "test-profile"],
                input="y\n"  # Confirm deletion
            )
            
            assert result.exit_code == 0
            mock_delete.assert_called_once_with("test-profile")
            assert "Profile 'test-profile' deleted successfully" in result.output
            assert "Default profile changed to 'other-profile'" in result.output
    
    def test_delete_default_profile_no_remaining(self, runner):
        """Test deleting the default profile when it's the last one."""
        with patch("langflow_cli.commands.env.get_default_profile", side_effect=["test-profile", None]), \
             patch("langflow_cli.commands.env.delete_profile") as mock_delete:
            
            result = runner.invoke(
                cli,
                ["env", "delete", "test-profile"],
                input="y\n"  # Confirm deletion
            )
            
            assert result.exit_code == 0
            mock_delete.assert_called_once_with("test-profile")
            assert "No default profile set" in result.output
    
    def test_delete_nonexistent_profile(self, runner):
        """Test deleting a profile that doesn't exist."""
        with patch("langflow_cli.commands.env.delete_profile", side_effect=ValueError("Profile 'test-profile' does not exist.")):
            result = runner.invoke(
                cli,
                ["env", "delete", "test-profile"],
                input="y\n"  # Confirm deletion
            )
            
            assert result.exit_code != 0
            assert "Profile 'test-profile' does not exist" in result.output
    
    def test_delete_profile_cancelled(self, runner):
        """Test cancelling profile deletion."""
        with patch("langflow_cli.commands.env.delete_profile") as mock_delete:
            result = runner.invoke(
                cli,
                ["env", "delete", "test-profile"],
                input="n\n"  # Cancel deletion
            )
            
            # When cancelled, delete_profile should not be called
            mock_delete.assert_not_called()
    
    def test_delete_profile_error_handling(self, runner):
        """Test error handling when deleting profile fails."""
        with patch("langflow_cli.commands.env.delete_profile", side_effect=Exception("Config error")):
            result = runner.invoke(
                cli,
                ["env", "delete", "test-profile"],
                input="y\n"  # Confirm deletion
            )
            
            assert result.exit_code != 0
            assert "Failed to delete profile" in result.output


class TestEnvVersion:
    """Tests for the 'env version' command."""
    
    def test_version_default_profile(self, runner, mock_api_client):
        """Test getting version using default profile."""
        with patch("langflow_cli.commands.env.LangflowAPIClient", return_value=mock_api_client), \
             patch("langflow_cli.commands.env.print_json") as mock_print_json:
            
            result = runner.invoke(cli, ["env", "version"])
            
            assert result.exit_code == 0
            mock_api_client.get_version.assert_called_once()
            mock_print_json.assert_called_once()
    
    def test_version_specific_profile(self, runner, mock_api_client):
        """Test getting version using a specific profile."""
        with patch("langflow_cli.commands.env.LangflowAPIClient", return_value=mock_api_client) as mock_client_class, \
             patch("langflow_cli.commands.env.print_json") as mock_print_json:
            
            result = runner.invoke(cli, ["env", "version", "--profile", "test-profile"])
            
            assert result.exit_code == 0
            mock_client_class.assert_called_once_with(profile_name="test-profile")
            mock_api_client.get_version.assert_called_once()
            mock_print_json.assert_called_once()
    
    def test_version_error_handling(self, runner):
        """Test error handling when getting version fails."""
        mock_client = MagicMock()
        mock_client.get_version.side_effect = Exception("API error")
        
        with patch("langflow_cli.commands.env.LangflowAPIClient", return_value=mock_client):
            result = runner.invoke(cli, ["env", "version"])
            
            assert result.exit_code != 0
            assert "Failed to get version" in result.output
    
    def test_version_api_client_init_error(self, runner):
        """Test error handling when API client initialization fails."""
        with patch("langflow_cli.commands.env.LangflowAPIClient", side_effect=ValueError("No profile found")):
            result = runner.invoke(cli, ["env", "version"])
            
            assert result.exit_code != 0
            assert "Failed to get version" in result.output

