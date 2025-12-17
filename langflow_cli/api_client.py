"""Langflow API client for making HTTP requests to the Langflow API."""

import requests
from typing import Optional, Dict, Any, List
from langflow_cli.config import load_profile


class LangflowAPIClient:
    """Client for interacting with the Langflow API."""
    
    def __init__(self, profile_name: Optional[str] = None):
        """
        Initialize the API client.
        
        Args:
            profile_name: Name of the profile to use. If None, uses default profile.
        """
        url, api_key = load_profile(profile_name)
        self.base_url = url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": api_key,
            "Content-Type": "application/json",
        })
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/api/v1/flows/")
            params: Query parameters
            json_data: JSON body data
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            if e.response.content:
                try:
                    error_data = e.response.json()
                    if "detail" in error_data:
                        error_msg += f": {error_data['detail']}"
                except ValueError:
                    error_msg += f": {e.response.text}"
            raise requests.exceptions.HTTPError(error_msg) from e
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Request failed: {str(e)}") from e
    
    # Settings methods
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self._request("GET", "/api/v1/config")
    
    # Flow methods
    def list_flows(self) -> List[Dict[str, Any]]:
        """List all flows."""
        response = self._request("GET", "/api/v1/flows/")
        # API might return a list directly or wrapped in an object
        if isinstance(response, list):
            return response
        return response.get("flows", [])
    
    def get_flow(self, flow_id: str) -> Dict[str, Any]:
        """Get flow details by ID."""
        return self._request("GET", f"/api/v1/flows/{flow_id}")
    
    def create_flow(self, name: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new flow."""
        payload = {"name": name}
        if data:
            payload.update(data)
        return self._request("POST", "/api/v1/flows/", json_data=payload)
    
    def update_flow(self, flow_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing flow."""
        return self._request("PATCH", f"/api/v1/flows/{flow_id}", json_data=data)
    
    def delete_flow(self, flow_id: str) -> None:
        """Delete a flow."""
        self._request("DELETE", f"/api/v1/flows/{flow_id}")
    
    # Project methods
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        response = self._request("GET", "/api/v1/projects/")
        # API might return a list directly or wrapped in an object
        if isinstance(response, list):
            return response
        return response.get("projects", [])
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details by ID."""
        return self._request("GET", f"/api/v1/projects/{project_id}")
    
    def create_project(self, name: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new project."""
        payload = {"name": name}
        if data:
            payload.update(data)
        return self._request("POST", "/api/v1/projects/", json_data=payload)
    
    def update_project(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing project."""
        return self._request("PATCH", f"/api/v1/projects/{project_id}", json_data=data)
    
    def delete_project(self, project_id: str) -> None:
        """Delete a project."""
        self._request("DELETE", f"/api/v1/projects/{project_id}")

