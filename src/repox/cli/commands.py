"""CLI commands for Repox."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from ..core.assistant import RepoxAssistant
from ..core.config import RepoxConfig
from ..processing.locator import FileLocator


class RepoxCLI:
    """Command-line interface for Repox."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def get_config(self, config_path: Optional[Path] = None, verbose: bool = False) -> RepoxConfig:
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
                self.console.print_exception()
            raise click.ClickException(f"Configuration error: {e}")
    
    def ask(self, question: str, repo: Path, config: Optional[Path], verbose: bool):
        """Ask a question about the repository."""
        try:
            repox_config = self.get_config(config, verbose)
            assistant = RepoxAssistant(repo, repox_config)
            
            with self.console.status("[bold green]🤔 Thinking..."):
                response = assistant.ask(question)
            
            self.console.print("\n🤖 [bold blue]Repox:[/bold blue]")
            self.console.print(response.answer)
            
            if verbose and response.context:
                self.console.print("\n📁 [dim]Context files used:[/dim]")
                for file_path in response.context.split('\n'):
                    if file_path.strip().startswith('File:'):
                        self.console.print(f"  • {file_path.strip()[5:].strip()}")
                        
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            if verbose:
                self.console.print_exception()
            raise click.ClickException(str(e))
    
    def find(self, query: str, repo: Path, config: Optional[Path], verbose: bool, 
             max_results: int, search_content: bool):
        """Find files relevant to a query."""
        try:
            repox_config = self.get_config(config, verbose)
            locator = FileLocator(repo, repox_config)
            
            with self.console.status("[bold green]🔍 Searching..."):
                result = locator.locate_files(query, max_results, search_content)
            
            if not result["located_files"]:
                self.console.print("[yellow]No relevant files found.[/yellow]")
                return
            
            self.console.print(f"\n🎯 Found {len(result['located_files'])} relevant files:")
            for file_path in result["located_files"]:
                self.console.print(f"  • {file_path}")
                
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            if verbose:
                self.console.print_exception()
            raise click.ClickException(str(e))
    
    def build(self, files: Optional[str], query: Optional[str], repo: Path, 
              config: Optional[Path], verbose: bool, output: Optional[Path]):
        """Build context from repository files."""
        try:
            if not files and not query:
                raise click.ClickException("Must specify either --files or --query")
            
            repox_config = self.get_config(config, verbose)
            assistant = RepoxAssistant(repo, repox_config)
            
            with self.console.status("[bold green]📋 Building context..."):
                if files:
                    file_list = [f.strip() for f in files.split(',')]
                    result = assistant.build_context(file_list)
                else:
                    result = assistant.build_context(query=query)
            
            if output:
                output.write_text(result.context)
                self.console.print(f"✅ Context saved to {output}")
            else:
                self.console.print("\n📋 [bold blue]Context:[/bold blue]")
                self.console.print(result.context)
                
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            if verbose:
                self.console.print_exception()
            raise click.ClickException(str(e))
    
    def info(self, repo: Path, config: Optional[Path], verbose: bool):
        """Show repository information."""
        try:
            repox_config = self.get_config(config, verbose)
            assistant = RepoxAssistant(repo, repox_config)
            
            with self.console.status("[bold green]📊 Analyzing repository..."):
                info = assistant.get_repository_info()
            
            self.console.print(f"\n📊 [bold blue]Repository Information:[/bold blue]")
            self.console.print(f"  📁 Path: {info.get('repository_path', 'Unknown')}")
            self.console.print(f"  📄 Files: {info.get('file_count', 'Unknown')}")
            self.console.print(f"  📏 Total size: {info.get('total_size', 'Unknown')}")
            
            if verbose and 'file_types' in info:
                self.console.print(f"  📋 File types: {', '.join(info['file_types'])}")
                
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            if verbose:
                self.console.print_exception()
            raise click.ClickException(str(e))
    
    def init(self, repo: Path):
        """Initialize Repox configuration."""
        try:
            config_path = repo / ".repox.json"
            
            if config_path.exists():
                self.console.print(f"[yellow]Configuration already exists at {config_path}[/yellow]")
                return
            
            # Create default configuration
            config = RepoxConfig()
            config.save_to_file(config_path)
            
            self.console.print(f"✅ Configuration created at {config_path}")
            self.console.print("\n📝 Next steps:")
            self.console.print("1. Set your OpenAI API key: export OPENAI_API_KEY='your-key'")
            self.console.print("2. Try: repox ask 'What does this repository do?'")
            self.console.print("3. Customize settings in .repox.json as needed")
            
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            raise click.ClickException(str(e))