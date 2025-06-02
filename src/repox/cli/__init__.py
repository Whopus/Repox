"""Command line interface for Repox."""

from .main import cli
from .commands import RepoxCLI

def main():
    """Entry point for the CLI."""
    cli()

__all__ = ['cli', 'RepoxCLI', 'main']