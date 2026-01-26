"""Git-like commands for flow management."""

import click
from langflow_cli.commands.git import remote
from langflow_cli.commands.git import branch
from langflow_cli.commands.git import checkout
from langflow_cli.commands.git import push
from langflow_cli.commands.git import pull


@click.group()
def git():
    """Git-like commands for managing flows in GitHub repositories."""
    pass


# Register all subcommands
remote.register_remote_commands(git)
branch.register_branch_command(git)
checkout.register_checkout_command(git)
push.register_push_command(git)
pull.register_pull_command(git)

# Register switch and pr commands when they're ready
try:
    from langflow_cli.commands.git import switch
    switch.register_switch_command(git)
except ImportError:
    pass

try:
    from langflow_cli.commands.git import pr
    pr.register_pr_command(git)
except ImportError:
    pass
