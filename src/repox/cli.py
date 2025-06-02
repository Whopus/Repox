"""Command-line interface for Repox - AI-Powered Code Assistant."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown

from . import __version__
from .assistant import RepoxAssistant
from .config import RepoxConfig
from .locator import FileLocator
from .models import ModelFactory


console = Console()


def print_banner():
    """Print Repox banner."""
    banner = Text("🤖 Repox", style="bold blue")
    banner.append(" - AI-Powered Code Assistant", style="dim")
    console.print(Panel(banner, border_style="blue"))


def get_config(config_path: Optional[Path] = None, verbose: bool = False) -> RepoxConfig:
    """Get configuration with proper error handling."""
    try:
        if config_path:
            return RepoxConfig.load_from_file(config_path)
        else:
            # Load from environment and file
            config = RepoxConfig.load_from_env()
            file_config = RepoxConfig.load_from_file()
            
            # Merge configurations
            config_data = file_config.model_dump()
            env_data = {k: v for k, v in config.model_dump().items() if v is not None}
            config_data.update(env_data)
            
            final_config = RepoxConfig(**config_data)
            final_config.verbose = verbose
            return final_config
    except Exception as e:
        if verbose:
            console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")
        config = RepoxConfig()
        config.verbose = verbose
        return config


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.pass_context
def cli(ctx, version):
    """🤖 Repox - AI-Powered Code Assistant
    
    Intelligent code analysis and Q&A for your repositories.
    
    Examples:
        repox ask "How does authentication work?"
        repox find "database models"
        repox build --files "src/auth.py,src/models.py"
        repox info --summary
    """
    if version:
        console.print(f"Repox version {__version__}")
        sys.exit(0)
    
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print("\n[dim]Use --help to see available commands[/dim]")


@cli.command()
@click.argument("question", required=True)
@click.option("--repo", "-r", type=click.Path(exists=True, path_type=Path), 
              default=Path.cwd(), help="Repository path")
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), 
              help="Configuration file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--preview", is_flag=True, help="Preview file selection only")
@click.option("--format", "output_format", type=click.Choice(["text", "markdown", "json"]), 
              default="text", help="Output format")
def ask(question: str, repo: Path, config: Optional[Path], verbose: bool, 
        preview: bool, output_format: str):
    """💬 Ask questions about your codebase.
    
    Examples:
        repox ask "How does the authentication system work?"
        repox ask "What are the main API endpoints?" --preview
        repox ask "Explain the database schema" --format markdown
    """
    try:
        repox_config = get_config(config, verbose)
        assistant = RepoxAssistant(repo, repox_config)
        
        if preview:
            # Show file selection preview
            if verbose:
                console.print("🔍 Analyzing question and selecting files...")
            
            selection = assistant.select_files(question)
            
            # Display selection
            table = Table(title="📁 File Selection Preview")
            table.add_column("File", style="cyan")
            table.add_column("Reason", style="green")
            
            for file_path in selection.selected_files:
                table.add_row(file_path, "Selected by AI")
            
            console.print(table)
            console.print(f"\n💭 Reasoning: {selection.reasoning}")
            return
        
        # Get full answer
        if verbose:
            console.print("🤖 Generating answer...")
        
        answer = assistant.ask(question)
        
        if output_format == "json":
            result = {
                "question": question,
                "answer": answer,
                "repository": str(repo)
            }
            console.print(json.dumps(result, indent=2))
        elif output_format == "markdown":
            md_content = f"# Question\n\n{question}\n\n# Answer\n\n{answer}"
            console.print(Markdown(md_content))
        else:
            console.print(f"\n[bold blue]Question:[/bold blue] {question}")
            console.print(f"\n[bold green]Answer:[/bold green]\n{answer}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument("query", required=True)
@click.option("--repo", "-r", type=click.Path(exists=True, path_type=Path), 
              default=Path.cwd(), help="Repository path")
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), 
              help="Configuration file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--limit", "-n", type=int, default=10, help="Maximum results")
@click.option("--format", "output_format", type=click.Choice(["table", "json", "simple"]), 
              default="table", help="Output format")
@click.option("--content", is_flag=True, help="Search file content (slower)")
def find(query: str, repo: Path, config: Optional[Path], verbose: bool, 
         limit: int, output_format: str, content: bool):
    """🔍 Find files and content in your repository.
    
    Examples:
        repox find "authentication"
        repox find "database models" --content
        repox find "test files" --format json --limit 5
    """
    try:
        repox_config = get_config(config, verbose)
        
        # Create AI model for file location
        model = ModelFactory.create_openai_model(
            repox_config.strong_model,
            repox_config.openai_api_key,
            repox_config.openai_base_url
        )
        
        locator = FileLocator(repo, repox_config, model, console)
        
        if verbose:
            console.print(f"🔍 Searching for: {query}")
        
        result = locator.locate_files(query, max_results=limit, search_content=content)
        
        if output_format == "json":
            console.print(json.dumps({
                "query": query,
                "files": result.located_files,
                "confidence": result.confidence,
                "reasoning": result.reasoning
            }, indent=2))
        elif output_format == "simple":
            for file_path in result.located_files:
                console.print(file_path)
        else:
            # Table format
            table = Table(title=f"🔍 Search Results for '{query}'")
            table.add_column("File", style="cyan")
            table.add_column("Matches", style="yellow")
            table.add_column("Reason", style="green")
            
            for file_path in result.located_files:
                matches = len(result.content_matches.get(file_path, []))
                reason = "AI analysis" if matches == 0 else f"{matches} matches"
                table.add_row(file_path, str(matches) if matches > 0 else "Filename", reason)
            
            console.print(table)
            console.print(f"\n💭 Reasoning: {result.reasoning}")
            console.print(f"🎯 Confidence: {result.confidence:.2f}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option("--files", help="Comma-separated list of files")
@click.option("--query", help="Query to select files automatically")
@click.option("--focus", help="Focus areas (e.g., 'auth,database,api')")
@click.option("--repo", "-r", type=click.Path(exists=True, path_type=Path), 
              default=Path.cwd(), help="Repository path")
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), 
              help="Configuration file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--compress", is_flag=True, help="Enable compression")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file")
@click.option("--format", "output_format", type=click.Choice(["markdown", "json"]), 
              default="markdown", help="Output format")
def build(files: Optional[str], query: Optional[str], focus: Optional[str],
          repo: Path, config: Optional[Path], verbose: bool, compress: bool,
          output: Optional[Path], output_format: str):
    """📋 Build context from repository files.
    
    Examples:
        repox build --files "src/auth.py,src/models.py"
        repox build --query "authentication system"
        repox build --focus "auth,security" --compress
        repox build --query "API endpoints" --output api_docs.md
    """
    try:
        if not files and not query:
            console.print("[red]Error: Must specify either --files or --query[/red]")
            sys.exit(1)
        
        repox_config = get_config(config, verbose)
        assistant = RepoxAssistant(repo, repox_config)
        
        if files:
            # Build from specific files
            file_list = [f.strip() for f in files.split(",")]
            if verbose:
                console.print(f"📋 Building context from {len(file_list)} files...")
            context = assistant.build_context_with_repomix(file_list)
        else:
            # Build from query
            if verbose:
                console.print(f"🔍 Finding files for query: {query}")
            selection = assistant.select_files(query)
            context = assistant.build_context_with_repomix(selection.selected_files)
        
        # Apply focus areas if specified
        if focus:
            focus_areas = [f.strip() for f in focus.split(",")]
            if verbose:
                console.print(f"🎯 Applying focus areas: {', '.join(focus_areas)}")
            # TODO: Implement focus area filtering
        
        # Apply compression if requested
        if compress:
            if verbose:
                console.print("🗜️ Applying compression...")
            # TODO: Implement compression
        
        # Output result
        if output:
            output.write_text(context)
            console.print(f"✅ Context saved to {output}")
        else:
            if output_format == "json":
                result = {
                    "context": context,
                    "files": file_list if files else selection.selected_files,
                    "compressed": compress
                }
                console.print(json.dumps(result, indent=2))
            else:
                console.print(context)
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option("--repo", "-r", type=click.Path(exists=True, path_type=Path), 
              default=Path.cwd(), help="Repository path")
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), 
              help="Configuration file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--summary", is_flag=True, help="Show repository summary")
@click.option("--files", is_flag=True, help="List processable files")
@click.option("--stats", is_flag=True, help="Show detailed statistics")
def info(repo: Path, config: Optional[Path], verbose: bool, summary: bool, 
         files: bool, stats: bool):
    """ℹ️ Show repository information.
    
    Examples:
        repox info --summary
        repox info --files
        repox info --stats
    """
    try:
        repox_config = get_config(config, verbose)
        assistant = RepoxAssistant(repo, repox_config)
        
        if summary or (not files and not stats):
            # Show summary
            summary_data = assistant.repository_analyzer.get_repository_summary()
            
            table = Table(title="📊 Repository Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in summary_data.items():
                if key == "largest_files":
                    value = ", ".join([f"{name} ({size} bytes)" for name, size in value[:3]])
                elif key == "file_types":
                    value = ", ".join([f"{ext}: {count}" for ext, count in list(value.items())[:5]])
                table.add_row(key.replace("_", " ").title(), str(value))
            
            console.print(table)
        
        if files:
            # List files
            processable_files = assistant.repository_analyzer.get_processable_files()
            
            console.print(f"\n📁 Processable Files ({len(processable_files)} total):")
            for file_path in sorted(processable_files):
                console.print(f"  📄 {file_path}")
        
        if stats:
            # Detailed statistics
            console.print("\n📈 Detailed Statistics:")
            # TODO: Implement detailed stats
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option("--repo", "-r", type=click.Path(path_type=Path), 
              default=Path.cwd(), help="Repository path")
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
def init(repo: Path, force: bool):
    """🚀 Initialize Repox configuration.
    
    Creates a .repox.json configuration file in the repository.
    """
    try:
        config_path = repo / ".repox.json"
        
        if config_path.exists() and not force:
            console.print(f"[yellow]Configuration already exists at {config_path}[/yellow]")
            console.print("Use --force to overwrite")
            return
        
        # Create default configuration
        config = RepoxConfig()
        config.save_to_file(config_path)
        
        console.print(f"✅ Configuration created at {config_path}")
        console.print("\n📝 Next steps:")
        console.print("1. Set your OpenAI API key: export OPENAI_API_KEY='your-key'")
        console.print("2. Try: repox ask 'What does this repository do?'")
        console.print("3. Customize settings in .repox.json as needed")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()