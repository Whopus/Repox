"""Command-line interface for Repox."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .assistant import RepoxAssistant
from .config import RepoxConfig
from .locator import FileLocator
from .models import ModelFactory


console = Console()


@click.group(invoke_without_command=True)
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
@click.option(
    "--question", "-q",
    help="Question to ask about the codebase"
)
@click.pass_context
def main(
    ctx: click.Context,
    repo: Path,
    config: Optional[Path],
    verbose: bool,
    init: bool,
    summary: bool,
    list_files: bool,
    preview: bool,
    version: bool,
    question: Optional[str],
) -> None:
    """Repox - AI-Powered Code Context Management Assistant
    
    Ask questions about your codebase and get intelligent answers.
    
    Examples:
        repox --question "How does authentication work?"
        repox --repo /path/to/project --question "What are the main components?"
        repox --preview --question "Explain the database schema"
        repox locate "authentication functions"
        repox context --files auth.py,login.py
    """
    
    # Store context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['repo'] = repo
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose
    
    # If no subcommand is invoked, handle the main functionality
    if ctx.invoked_subcommand is None:
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


@main.command()
@click.argument("query")
@click.option(
    "--format", "-f",
    type=click.Choice(["table", "json", "simple"]),
    default="table",
    help="Output format"
)
@click.option(
    "--max-results", "-n",
    type=int,
    default=10,
    help="Maximum number of results to show"
)
@click.pass_context
def locate(ctx: click.Context, query: str, format: str, max_results: int) -> None:
    """Locate files and content based on a query.
    
    This command helps you find files that are relevant to your query,
    including content-based search within files.
    
    Examples:
        repox locate "authentication functions"
        repox locate "database models" --format json
        repox locate "test files" --max-results 5
    """
    
    try:
        # Get configuration from context
        repo = ctx.obj['repo']
        config_path = ctx.obj['config']
        verbose = ctx.obj['verbose']
        
        # Load configuration
        repox_config = RepoxConfig()
        if config_path:
            repox_config = RepoxConfig.load_from_file(config_path)
        else:
            repox_config = RepoxConfig().get_effective_config()
        
        if verbose:
            repox_config.verbose = True
        
        # Create AI model for locator
        strong_model = ModelFactory.create_openai_model(
            model_name=repox_config.strong_model,
            api_key=repox_config.openai_api_key,
            base_url=repox_config.openai_base_url,
        )
        
        # Initialize locator
        locator = FileLocator(repo, repox_config, strong_model)
        
        # Perform location search
        with console.status("🔍 Locating files..."):
            result = locator.locate_files(query)
        
        # Display results based on format
        if format == "json":
            console.print(json.dumps(result, indent=2))
        elif format == "simple":
            for file_path in result["located_files"][:max_results]:
                console.print(file_path)
        else:  # table format
            _display_locate_results(result, max_results)
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@main.command()
@click.option(
    "--files",
    help="Comma-separated list of files to include in context"
)
@click.option(
    "--query",
    help="Query to optimize context for"
)
@click.option(
    "--focus",
    help="Comma-separated list of focus areas (e.g., 'tests,docs,config')"
)
@click.option(
    "--compression",
    is_flag=True,
    help="Enable compression to reduce context size"
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: stdout)"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    help="Output format"
)
@click.pass_context
def context(
    ctx: click.Context,
    files: Optional[str],
    query: Optional[str],
    focus: Optional[str],
    compression: bool,
    output: Optional[Path],
    format: str,
) -> None:
    """Build optimized context from repository files.
    
    This command creates a well-structured context from your repository
    that can be used for AI analysis or documentation.
    
    Examples:
        repox context --files "src/main.py,src/config.py"
        repox context --query "authentication system" --focus "auth,security"
        repox context --compression --output context.md
    """
    
    try:
        # Get configuration from context
        repo = ctx.obj['repo']
        config_path = ctx.obj['config']
        verbose = ctx.obj['verbose']
        
        # Load configuration
        repox_config = RepoxConfig()
        if config_path:
            repox_config = RepoxConfig.load_from_file(config_path)
        else:
            repox_config = RepoxConfig().get_effective_config()
        
        if verbose:
            repox_config.verbose = True
        
        # Initialize assistant for context building
        assistant = RepoxAssistant(repo_path=str(repo), config=repox_config)
        
        # Parse input parameters
        selected_files = files.split(',') if files else None
        focus_areas = focus.split(',') if focus else None
        
        # If query is provided but no files, use locator to find relevant files
        if query and not selected_files:
            strong_model = ModelFactory.create_openai_model(
                model_name=repox_config.strong_model,
                api_key=repox_config.openai_api_key,
                base_url=repox_config.openai_base_url,
            )
            
            locator = FileLocator(repo, repox_config, strong_model)
            
            with console.status("🔍 Finding relevant files..."):
                location_result = locator.locate_files(query)
            
            selected_files = location_result["located_files"]
            
            if verbose:
                console.print(f"[blue]Found {len(selected_files)} relevant files for query[/blue]")
        
        # Build context
        with console.status("📦 Building context..."):
            from .repomix_integration import RepomixIntegration
            
            repomix_integration = RepomixIntegration(repo, repox_config)
            context_result = repomix_integration.build_context(
                selected_files=selected_files,
                focus_areas=focus_areas,
                compression_enabled=compression,
                max_size=repox_config.max_context_size,
            )
        
        # Format output
        if format == "json":
            output_content = json.dumps(context_result, indent=2)
        else:  # markdown
            output_content = context_result["content"]
            
            # Add metadata header
            metadata = context_result["metadata"]
            header = f"""# Repository Context

**Generated by Repox v{__version__}**

- **Repository**: {repo}
- **Total Files**: {metadata['total_files']}
- **Total Size**: {metadata['total_size']:,} bytes
- **Compression**: {'Enabled' if metadata['compression_enabled'] else 'Disabled'}
- **Focus Areas**: {', '.join(metadata['focus_areas']) if metadata['focus_areas'] else 'None'}

---

"""
            output_content = header + output_content
        
        # Output results
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(output_content)
            console.print(f"[green]✅ Context saved to {output}[/green]")
        else:
            console.print(output_content)
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


def _display_locate_results(result: Dict[str, Any], max_results: int) -> None:
    """Display location results in table format."""
    
    # Main results table
    table = Table(title="🔍 File Location Results")
    table.add_column("File", style="cyan", no_wrap=True)
    table.add_column("Matches", style="yellow")
    table.add_column("Reason", style="green")
    
    # Add located files
    for i, file_path in enumerate(result["located_files"][:max_results]):
        matches = len(result["content_matches"].get(file_path, []))
        match_text = f"{matches} matches" if matches > 0 else "Filename match"
        
        table.add_row(
            file_path,
            match_text,
            "AI analysis"
        )
    
    console.print(table)
    
    # Show summary
    total_files = len(result["located_files"])
    total_matches = sum(len(matches) for matches in result["content_matches"].values())
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  📁 Files found: {total_files}")
    console.print(f"  🔍 Content matches: {total_matches}")
    console.print(f"  🎯 Confidence: {result['confidence']:.2f}")
    console.print(f"  📋 Strategy: {result['search_strategy']}")
    
    # Show reasoning
    console.print(f"\n[bold blue]💭 Reasoning:[/bold blue]")
    console.print(result["reasoning"])


if __name__ == "__main__":
    main()