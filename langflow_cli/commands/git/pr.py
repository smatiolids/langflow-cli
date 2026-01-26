"""Pull request command."""

import os
import click
from typing import Optional, Tuple
from rich.console import Console
from langflow_cli.git_config import (
    get_current_remote,
    get_current_branch,
)
from langflow_cli.git_client import GitHubClient
from langflow_cli.config import get_default_profile

console = Console()


def register_pr_command(git_group: click.Group) -> None:
    """Register PR command with the git group."""
    
    @git_group.command("pr")
    @click.option("--source-branch", help="Source branch (defaults to current branch)")
    @click.option("--target-branch", help="Target branch (defaults to repository default branch)")
    @click.option("--title", help="PR title (auto-generated if not provided)")
    @click.option("--body", help="PR body text (auto-generated if not provided)")
    @click.option("--body-file", help="Path to markdown file for PR body")
    @click.option("--draft", is_flag=True, help="Create as draft PR")
    @click.option("--remote", help="Remote name (overrides current selection)")
    @click.option("--profile", help="Profile to use (overrides default)")
    def pr(
        source_branch: Optional[str],
        target_branch: Optional[str],
        title: Optional[str],
        body: Optional[str],
        body_file: Optional[str],
        draft: bool,
        remote: Optional[str],
        profile: Optional[str]
    ):
        """Create a pull request on GitHub."""
        try:
            profile_name = profile or get_default_profile()
            if not profile_name:
                raise ValueError("No profile selected. Use 'langflow-cli env register' to create one.")
            
            remote_name = remote or get_current_remote(profile_name)
            if not remote_name:
                raise ValueError("No remote selected. Use 'langflow-cli git remote select <name>' first.")
            
            client = GitHubClient(remote_name)
            
            # Get source and target branches
            source = source_branch or get_current_branch(profile_name)
            if not source:
                raise ValueError("No source branch specified. Use --source-branch or select a branch with 'langflow-cli git checkout <branch>'")
            
            target = target_branch or client.repo.default_branch
            
            # Validate branches exist
            branches = client.get_branches()
            if source not in branches:
                raise ValueError(f"Source branch '{source}' not found")
            if target not in branches:
                raise ValueError(f"Target branch '{target}' not found")
            
            # Check if source == target
            if source == target:
                raise ValueError(f"Source and target branches cannot be the same: {source}")
            
            # Check if PR already exists
            existing_pr = client.pr_exists(source, target)
            if existing_pr:
                console.print(f"[yellow]⚠[/yellow]  Pull request already exists: {existing_pr.html_url}")
                if not click.confirm("Continue anyway?"):
                    raise click.Abort()
            
            # Handle body file
            if body_file:
                if not os.path.exists(body_file):
                    raise ValueError(f"Body file not found: {body_file}")
                if not os.path.isfile(body_file):
                    raise ValueError(f"Body file is not a file: {body_file}")
                try:
                    with open(body_file, 'r', encoding='utf-8') as f:
                        body = f.read()
                except Exception as e:
                    raise ValueError(f"Failed to read body file: {str(e)}")
            
            # Auto-generate title/body if not provided
            if not title or not body:
                generated_title, generated_body = _generate_pr_details(client, source)
                title = title or generated_title
                body = body or generated_body
            
            # Create PR
            console.print(f"[cyan]Creating pull request from '{source}' to '{target}'...[/cyan]")
            pr = client.create_pull_request(title, body, source, target, draft)
            
            console.print(f"[green]✓[/green] Pull request created successfully")
            console.print(f"[dim]PR #{pr.number}: {pr.title}[/dim]")
            console.print(f"[dim]URL: {pr.html_url}[/dim]")
        except ValueError as e:
            console.print(f"[red]✗[/red] {str(e)}")
            raise click.Abort()
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to create pull request: {str(e)}")
            raise click.Abort()


def _generate_pr_details(client: GitHubClient, branch: str) -> Tuple[str, str]:
    """
    Generate PR title and body from branch name and recent commits.
    
    Args:
        client: GitHub client instance
        branch: Branch name
        
    Returns:
        Tuple of (title, body)
    """
    # Generate title from branch name
    title = branch.replace("_", " ").replace("-", " ").title()
    
    # Get recent commits
    try:
        commits = client.get_recent_commits(branch, count=10)
        if commits:
            body_lines = ["## Changes\n"]
            for commit in commits[:10]:
                commit_msg = commit.commit.message.split('\n')[0]  # First line only
                body_lines.append(f"- {commit_msg}")
            body = "\n".join(body_lines)
        else:
            body = f"Pull request from branch `{branch}`"
    except Exception:
        body = f"Pull request from branch `{branch}`"
    
    return title, body
