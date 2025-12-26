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
        except requests.exceptions.SSLError as e:
            if "WRONG_VERSION_NUMBER" in str(e):
                error_msg = (
                    f"SSL Error: {str(e)}\n"
                    "This usually happens when an HTTPS request is made to an HTTP server. "
                    "Try re-registering your environment using 'http://' instead of 'https://'."
                )
                raise requests.exceptions.SSLError(error_msg) from e
            raise requests.exceptions.SSLError(f"SSL Error: {str(e)}") from e
        except requests.exceptions.RequestException as e:
            error_string = str(e)
            if "WRONG_VERSION_NUMBER" in error_string:
                hint = (
                    "\n\n[bold yellow]Hint:[/bold yellow] This SSL error typically means you're trying to reach an HTTP server using HTTPS.\n"
                    "Try re-registering your environment using 'http://' instead of 'https://':\n"
                    "  langflow-cli env register local --url http://localhost:7860 --api-key <your-key>"
                )
                raise requests.exceptions.RequestException(f"Request failed: {error_string}{hint}") from e
            raise requests.exceptions.RequestException(f"Request failed: {error_string}") from e
    
    # Settings methods
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self._request("GET", "/api/v1/config")
    
    def get_version(self) -> Dict[str, Any]:
        """Get Langflow version information."""
        return self._request("GET", "/api/v1/version")
    
    # Flow methods
    def list_flows(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all flows, optionally filtered by project ID.
        Flows are enriched with project_id and project_name.
        
        Args:
            project_id: Optional project ID to filter flows by
            
        Returns:
            List of flow dictionaries, each enriched with project_id and project_name
        """
        response = self._request("GET", "/api/v1/flows/")
        # API might return a list directly or wrapped in an object
        if isinstance(response, list):
            flows = response
        else:
            flows = response.get("flows", [])
        
        # Filter by project_id if provided
        if project_id:
            filtered_flows = []
            for flow in flows:
                flow_project_id = flow.get("folder_id") or flow.get("project_id")
                if str(flow_project_id) == str(project_id):
                    filtered_flows.append(flow)
            flows = filtered_flows
        
        # Enrich flows with project information
        projects_list = self.list_projects()
        projects_dict = {}
        for project in projects_list:
            proj_id = project.get("id", project.get("project_id"))
            if proj_id:
                projects_dict[str(proj_id)] = project
        
        # Add project_id and project_name to each flow
        for flow in flows:
            flow["project_id"] = flow.get("folder_id") or flow.get("project_id")
            if flow["project_id"]:
                project = projects_dict.get(str(flow["project_id"]))
                if project:
                    flow["project_name"] = project.get("name", "N/A")
                else:
                    flow["project_name"] = "N/A"
        
        # Sort by project name first, then flow name (case-insensitive)
        flows.sort(key=lambda x: (
            (x.get('project_name', 'N/A') or 'N/A').lower() if x.get('project_name') != "N/A" else "zzz",
            (x.get('name', 'Unnamed') or 'Unnamed').lower()
        ))
        
        return flows
    
    def get_flow(self, flow_id: str) -> Dict[str, Any]:
        """Get flow details by ID."""

        flow = self._request("GET", f"/api/v1/flows/{flow_id}")

        if not flow:
            raise ValueError(f"Flow '{flow_id}' not found")
            
        flow["project_id"] = flow.get("folder_id") or flow.get("project_id") or None
        
        if flow["project_id"]:
            project = self.get_project(flow["project_id"])
            flow["project_name"] = project.get("name", "Unknown")
        return flow
    
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
    
    def download_project(self, project_id: str) -> bytes:
        """
        Download a project as a zip file.
        
        Args:
            project_id: The project ID to download
            
        Returns:
            Binary content of the zip file
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.base_url}/api/v1/projects/download/{project_id}"
        
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            return response.content
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

