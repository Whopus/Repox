"""Command-line interface for Repox."""

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .assistant import RepoxAssistant
from .config import RepoxConfig


console = Console()


@click.command()
@click.argument("question", required=False)
@click.option(
    "--repo", "-r",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="Repository path (default: current directory)"
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Path to configuration file"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output"
)
@click.option(
    "--init",
    is_flag=True,
    help="Initialize configuration file in current directory"
)
@click.option(
    "--summary",
    is_flag=True,
    help="Show repository summary"
)
@click.option(
    "--list-files",
    is_flag=True,
    help="List processable files"
)
@click.option(
    "--preview",
    is_flag=True,
    help="Preview file selection for question without generating answer"
)
@click.option(
    "--version",
    is_flag=True,
    help="Show version information"
)
def main(
    question: Optional[str],
    repo: Path,
    config: Optional[Path],
    verbose: bool,
    init: bool,
    summary: bool,
    list_files: bool,
    preview: bool,
    version: bool,
) -> None:
    """Repox - AI-Powered Code Context Management Assistant
    
    Ask questions about your codebase and get intelligent answers.
    
    Examples:
        repox "How does authentication work?"
        repox --repo /path/to/project "What are the main components?"
        repox --preview "Explain the database schema"
    """
    
    if version:
        console.print(f"Repox version {__version__}")
        return
    
    if init:
        _init_config()
        return
    
    try:
        # Load configuration
        repox_config = RepoxConfig()
        if config:
            repox_config = RepoxConfig.load_from_file(config)
        else:
            repox_config = RepoxConfig().get_effective_config()
        
        # Override verbose setting from CLI
        if verbose:
            repox_config.verbose = True
        
        # Initialize assistant
        assistant = RepoxAssistant(repo_path=str(repo), config=repox_config)
        
        if summary:
            _show_repository_summary(assistant)
            return
        
        if list_files:
            _list_processable_files(assistant)
            return
        
        if not question:
            # Interactive mode
            _interactive_mode(assistant)
        else:
            # Single question mode
            if preview:
                _preview_file_selection(assistant, question)
            else:
                answer = assistant.ask(question)
                if not verbose:
                    console.print(answer)
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


def _init_config() -> None:
    """Initialize configuration file."""
    config_path = Path.cwd() / ".repox.json"
    
    if config_path.exists():
        if not click.confirm(f"Configuration file {config_path} already exists. Overwrite?"):
            return
    
    config = RepoxConfig()
    config.save_to_file(config_path)
    
    console.print(f"[green]✅ Configuration file created: {config_path}[/green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Set your OpenAI API key: export OPENAI_API_KEY='your-key'")
    console.print("2. Optionally configure models: export REPOX_STRONG_MODEL='gpt-4'")
    console.print("3. Edit .repox.json to customize settings")


def _show_repository_summary(assistant: RepoxAssistant) -> None:
    """Show repository summary."""
    summary = assistant.get_repository_summary()
    
    table = Table(title="Repository Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Repository Path", summary["repository_path"])
    table.add_row("Total Files", str(summary["total_files"]))
    table.add_row("Total Size", f"{summary['total_size']:,} bytes")
    
    # Show file types
    file_types = summary["file_types"]
    top_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:5]
    types_str = ", ".join([f"{ext}: {count}" for ext, count in top_types])
    table.add_row("Top File Types", types_str)
    
    # Show largest files
    largest_files = summary["largest_files"][:5]
    files_str = "\n".join([f"{path} ({size:,} bytes)" for path, size in largest_files])
    table.add_row("Largest Files", files_str)
    
    console.print(table)


def _list_processable_files(assistant: RepoxAssistant) -> None:
    """List processable files."""
    files = assistant.list_processable_files()
    
    console.print(f"[bold]Processable Files ({len(files)} total):[/bold]\n")
    
    for file_path in sorted(files):
        console.print(f"  📄 {file_path}")


def _preview_file_selection(assistant: RepoxAssistant, question: str) -> None:
    """Preview file selection for a question."""
    preview = assistant.preview_file_selection(question)
    
    console.print(Panel(
        f"[bold blue]Question:[/bold blue] {question}",
        title="🔍 File Selection Preview",
        border_style="blue"
    ))
    
    console.print(f"\n[bold green]Selected Files ({len(preview['valid_files'])}):[/bold green]")
    for file_path in preview['valid_files']:
        console.print(f"  ✅ {file_path}")
    
    if preview['invalid_files']:
        console.print(f"\n[bold red]Invalid Files ({len(preview['invalid_files'])}):[/bold red]")
        for file_info in preview['invalid_files']:
            console.print(f"  ❌ {file_info}")
    
    console.print(f"\n[bold yellow]Reasoning:[/bold yellow]")
    console.print(preview['reasoning'])


def _interactive_mode(assistant: RepoxAssistant) -> None:
    """Run in interactive mode."""
    console.print(Panel(
        "[bold blue]Welcome to Repox![/bold blue]\n\n"
        "Ask questions about your codebase. Type 'quit' or 'exit' to leave.\n"
        "Commands:\n"
        "  - 'summary': Show repository summary\n"
        "  - 'files': List processable files\n"
        "  - 'preview <question>': Preview file selection",
        title="🤖 Interactive Mode",
        border_style="blue"
    ))
    
    while True:
        try:
            question = console.input("\n[bold cyan]❓ Your question:[/bold cyan] ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'q']:
                console.print("[bold green]👋 Goodbye![/bold green]")
                break
            
            if question.lower() == 'summary':
                _show_repository_summary(assistant)
                continue
            
            if question.lower() == 'files':
                _list_processable_files(assistant)
                continue
            
            if question.lower().startswith('preview '):
                preview_question = question[8:].strip()
                if preview_question:
                    _preview_file_selection(assistant, preview_question)
                else:
                    console.print("[red]Please provide a question for preview[/red]")
                continue
            
            # Generate answer
            answer = assistant.ask(question)
            console.print(Panel(
                answer,
                title="💡 Answer",
                border_style="green"
            ))
        
        except KeyboardInterrupt:
            console.print("\n[bold green]👋 Goodbye![/bold green]")
            break
        except EOFError:
            console.print("\n[bold green]👋 Goodbye![/bold green]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    main()