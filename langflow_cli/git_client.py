"""GitHub API client for repository operations."""

import json
import re
from typing import List, Optional, Dict, Any
from github import Github
from github.GithubException import GithubException
from langflow_cli.git_config import get_remote


class GitHubClient:
    """Client for interacting with GitHub repositories via API."""
    
    def __init__(self, remote_name: str):
        """
        Initialize GitHub client.
        
        Args:
            remote_name: Name of the remote to use
            
        Raises:
            ValueError: If remote doesn't exist or authentication fails
        """
        remote_config = get_remote(remote_name)
        self.url = remote_config["url"]
        self.token = remote_config.get("token")
        
        if not self.token:
            raise ValueError("Token required for GitHub authentication. Please provide a token when adding the remote.")
        
        # Extract domain, owner and repo from URL
        # Support both HTTPS and SSH formats:
        # - https://github.com/owner/repo or https://<domain>/owner/repo.git
        # - git@github.com:owner/repo.git or git@<domain>:owner/repo.git
        # - ssh://git@github.com/owner/repo.git or ssh://git@<domain>/owner/repo.git
        https_match = re.match(r"https?://([^/]+)/([^/]+)/([^/]+?)(?:\.git)?/?$", self.url)
        ssh_match = re.match(r"(?:ssh://)?git@([^:/]+)[:/]([^/]+)/([^/]+?)(?:\.git)?/?$", self.url)
        
        if https_match:
            self.domain = https_match.group(1)
            self.owner = https_match.group(2)
            self.repo_name = https_match.group(3)
        elif ssh_match:
            self.domain = ssh_match.group(1)
            self.owner = ssh_match.group(2)
            self.repo_name = ssh_match.group(3)
        else:
            raise ValueError(f"Invalid GitHub URL format: {self.url}")
        
        # Determine base URL for GitHub API
        # For GitHub Enterprise (non-github.com), use /api/v3 endpoint
        if self.domain == "github.com":
            self.base_url = None  # Use default GitHub API
        else:
            # For GitHub Enterprise, construct API base URL
            # Assume HTTPS and standard /api/v3 path
            self.base_url = f"https://{self.domain}/api/v3"
        
        # Initialize GitHub client with token
        if self.base_url:
            self.github = Github(base_url=self.base_url, login_or_token=self.token)
        else:
            self.github = Github(self.token)
        
        self.repo = self.github.get_repo(f"{self.owner}/{self.repo_name}")
    
    def get_branches(self) -> List[str]:
        """
        Get list of all branches in the repository.
        
        Returns:
            List of branch names
        """
        try:
            branches = self.repo.get_branches()
            return [branch.name for branch in branches]
        except GithubException as e:
            raise ValueError(f"Failed to get branches: {str(e)}")
    
    def get_file(self, file_path: str, branch: Optional[str] = None) -> str:
        """
        Get file contents from repository.
        
        Args:
            file_path: Path to file in repository
            branch: Branch name (defaults to default branch)
            
        Returns:
            File contents as string
            
        Raises:
            ValueError: If file doesn't exist
        """
        try:
            if branch:
                contents = self.repo.get_contents(file_path, ref=branch)
            else:
                contents = self.repo.get_contents(file_path)
            
            if contents.encoding == "base64":
                import base64
                return base64.b64decode(contents.content).decode("utf-8")
            return contents.decoded_content.decode("utf-8")
        except GithubException as e:
            if e.status == 404:
                raise ValueError(f"File not found: {file_path}")
            raise ValueError(f"Failed to get file: {str(e)}")
    
    def file_exists(self, file_path: str, branch: Optional[str] = None) -> bool:
        """
        Check if a file exists in the repository.
        
        Args:
            file_path: Path to file in repository
            branch: Branch name (defaults to default branch)
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            if branch:
                self.repo.get_contents(file_path, ref=branch)
            else:
                self.repo.get_contents(file_path)
            return True
        except GithubException as e:
            if e.status == 404:
                return False
            raise ValueError(f"Failed to check file existence: {str(e)}")
    
    def create_or_update_file(
        self,
        file_path: str,
        content: str,
        message: str,
        branch: Optional[str] = None
    ) -> None:
        """
        Create or update a file in the repository.
        
        Args:
            file_path: Path to file in repository
            content: File contents
            message: Commit message
            branch: Branch name (defaults to default branch)
            
        Raises:
            ValueError: If operation fails
        """
        try:
            target_branch = branch or self.repo.default_branch
            
            # Check if file exists
            try:
                if branch:
                    existing_file = self.repo.get_contents(file_path, ref=branch)
                else:
                    existing_file = self.repo.get_contents(file_path)
                
                # Update existing file
                self.repo.update_file(
                    file_path,
                    message,
                    content,
                    existing_file.sha,
                    branch=target_branch
                )
            except GithubException as e:
                if e.status == 404:
                    # Create new file
                    self.repo.create_file(
                        file_path,
                        message,
                        content,
                        branch=target_branch
                    )
                else:
                    raise
        except GithubException as e:
            raise ValueError(f"Failed to create/update file: {str(e)}")
    
    def delete_file(
        self,
        file_path: str,
        message: str,
        branch: Optional[str] = None
    ) -> None:
        """
        Delete a file from the repository.
        
        Args:
            file_path: Path to file in repository
            message: Commit message
            branch: Branch name (defaults to default branch)
            
        Raises:
            ValueError: If file doesn't exist or operation fails
        """
        try:
            target_branch = branch or self.repo.default_branch
            
            if branch:
                file = self.repo.get_contents(file_path, ref=branch)
            else:
                file = self.repo.get_contents(file_path)
            
            self.repo.delete_file(
                file_path,
                message,
                file.sha,
                branch=target_branch
            )
        except GithubException as e:
            if e.status == 404:
                raise ValueError(f"File not found: {file_path}")
            raise ValueError(f"Failed to delete file: {str(e)}")
    
    def list_files_in_directory(
        self,
        directory_path: str = "",
        branch: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List files in a directory.
        
        Args:
            directory_path: Path to directory (empty string for root)
            branch: Branch name (defaults to default branch)
            
        Returns:
            List of file/directory info dictionaries with 'path', 'type', 'name' keys
        """
        try:
            if branch:
                contents = self.repo.get_contents(directory_path, ref=branch)
            else:
                contents = self.repo.get_contents(directory_path)
            
            # Handle single file vs list
            if not isinstance(contents, list):
                contents = [contents]
            
            result = []
            for item in contents:
                result.append({
                    "path": item.path,
                    "type": item.type,  # 'file' or 'dir'
                    "name": item.name,
                    "size": item.size if item.type == "file" else None
                })
            
            return result
        except GithubException as e:
            if e.status == 404:
                return []  # Directory doesn't exist
            raise ValueError(f"Failed to list directory: {str(e)}")
    
    def find_files_by_pattern(
        self,
        pattern: str,
        directory_path: str = "",
        branch: Optional[str] = None
    ) -> List[str]:
        """
        Find files matching a pattern (recursive search).
        
        Args:
            pattern: Filename pattern to search for (supports wildcards)
            directory_path: Starting directory path
            branch: Branch name (defaults to default branch)
            
        Returns:
            List of matching file paths
        """
        import fnmatch
        
        matches = []
        files = self.list_files_in_directory(directory_path, branch)
        
        for item in files:
            if item["type"] == "file":
                if fnmatch.fnmatch(item["name"], pattern):
                    matches.append(item["path"])
            elif item["type"] == "dir":
                # Recursively search subdirectories
                sub_matches = self.find_files_by_pattern(
                    pattern,
                    item["path"],
                    branch
                )
                matches.extend(sub_matches)
        
        return matches
    
    def create_branch(self, branch_name: str, source_branch: Optional[str] = None) -> None:
        """
        Create a new branch from a source branch.
        
        Args:
            branch_name: Name of the branch to create
            source_branch: Source branch to create from (defaults to default branch)
            
        Raises:
            ValueError: If branch already exists or operation fails
        """
        try:
            source = source_branch or self.repo.default_branch
            
            # Get the SHA of the source branch
            source_ref = self.repo.get_git_ref(f"heads/{source}")
            source_sha = source_ref.object.sha
            
            # Create new branch
            self.repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source_sha)
        except GithubException as e:
            if e.status == 422:
                # 422 usually means branch already exists
                raise ValueError(f"Branch '{branch_name}' already exists")
            raise ValueError(f"Failed to create branch: {str(e)}")
    
    def delete_branch(self, branch_name: str) -> None:
        """
        Delete a branch.
        
        Args:
            branch_name: Name of the branch to delete
            
        Raises:
            ValueError: If branch is the default branch, doesn't exist, or operation fails
        """
        try:
            # Prevent deletion of default branch
            if branch_name == self.repo.default_branch:
                raise ValueError(f"Cannot delete default branch '{branch_name}'")
            
            # Get the branch reference
            ref = self.repo.get_git_ref(f"heads/{branch_name}")
            ref.delete()
        except GithubException as e:
            if e.status == 404:
                raise ValueError(f"Branch '{branch_name}' not found")
            raise ValueError(f"Failed to delete branch: {str(e)}")
    
    def create_pull_request(
        self,
        title: str,
        body: str,
        head: str,
        base: str,
        draft: bool = False
    ):
        """
        Create a pull request.
        
        Args:
            title: PR title
            body: PR body/description
            head: Source branch name
            base: Target branch name
            draft: Whether to create as draft PR
            
        Returns:
            Pull request object
            
        Raises:
            ValueError: If operation fails
        """
        try:
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base,
                draft=draft
            )
            return pr
        except GithubException as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                raise ValueError(f"Pull request from '{head}' to '{base}' already exists")
            raise ValueError(f"Failed to create pull request: {str(e)}")
    
    def get_recent_commits(self, branch: str, count: int = 10) -> List:
        """
        Get recent commits from a branch.
        
        Args:
            branch: Branch name
            count: Number of commits to retrieve (default: 10)
            
        Returns:
            List of commit objects
        """
        try:
            commits = self.repo.get_commits(sha=branch)
            return list(commits[:count])
        except GithubException as e:
            raise ValueError(f"Failed to get commits: {str(e)}")
    
    def pr_exists(self, head: str, base: str):
        """
        Check if a pull request already exists between two branches.
        
        Args:
            head: Source branch name
            base: Target branch name
            
        Returns:
            Pull request object if exists, None otherwise
        """
        try:
            # Format: owner:branch_name for head
            head_full = f"{self.owner}:{head}"
            pulls = self.repo.get_pulls(state="open", head=head_full, base=base)
            
            # Check if any PR matches
            for pr in pulls:
                if pr.head.ref == head and pr.base.ref == base:
                    return pr
            
            return None
        except GithubException:
            return None
    
    @staticmethod
    def sanitize_name(name: str, max_length: int = 50) -> str:
        """
        Sanitize a name for use as a folder or filename.
        
        Args:
            name: Name to sanitize
            max_length: Maximum length of sanitized name
            
        Returns:
            Sanitized name
        """
        # Keep alphanumeric, spaces, underscores, hyphens
        sanitized = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_'))
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        return sanitized

