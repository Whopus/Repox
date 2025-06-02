"""Interactive demo for Repox."""

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

# Add the src directory to the path so we can import repox
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from repox import RepoxAssistant, RepoxConfig


console = Console()


def check_environment():
    """Check if the environment is properly configured."""
    if not os.getenv("OPENAI_API_KEY"):
        console.print(Panel(
            "[bold red]Missing Configuration[/bold red]\n\n"
            "Please set the following environment variables:\n"
            "• OPENAI_API_KEY: Your OpenAI API key\n\n"
            "Optional:\n"
            "• OPENAI_BASE_URL: Custom API base URL\n"
            "• REPOX_STRONG_MODEL: Strong model name (default: gpt-4)\n"
            "• REPOX_WEAK_MODEL: Weak model name (default: gpt-3.5-turbo)",
            title="⚠️  Configuration Required",
            border_style="red"
        ))
        return False
    
    return True


def show_configuration():
    """Show current configuration."""
    config = RepoxConfig().get_effective_config()
    
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Strong Model", config.strong_model)
    table.add_row("Weak Model", config.weak_model)
    table.add_row("API Base URL", config.openai_base_url)
    table.add_row("Max File Size", f"{config.max_file_size:,} bytes")
    table.add_row("Max Context Size", f"{config.max_context_size:,} chars")
    table.add_row("Max Files per Request", str(config.max_files_per_request))
    
    console.print(table)


def demo_repository_analysis(assistant):
    """Demo repository analysis features."""
    console.print(Panel(
        "[bold blue]Repository Analysis Demo[/bold blue]",
        border_style="blue"
    ))
    
    # Show repository summary
    console.print("\n[bold]📊 Repository Summary[/bold]")
    summary = assistant.get_repository_summary()
    
    summary_table = Table()
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Files", str(summary['total_files']))
    summary_table.add_row("Total Size", f"{summary['total_size']:,} bytes")
    summary_table.add_row("Repository Path", summary['repository_path'])
    
    console.print(summary_table)
    
    # Show file types
    if summary['file_types']:
        console.print("\n[bold]📁 File Types[/bold]")
        types_table = Table()
        types_table.add_column("Extension", style="cyan")
        types_table.add_column("Count", style="green")
        
        for ext, count in sorted(summary['file_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
            types_table.add_row(ext, str(count))
        
        console.print(types_table)
    
    # Show largest files
    if summary['largest_files']:
        console.print("\n[bold]📄 Largest Files[/bold]")
        files_table = Table()
        files_table.add_column("File", style="cyan")
        files_table.add_column("Size", style="green")
        
        for file_path, size in summary['largest_files'][:10]:
            files_table.add_row(file_path, f"{size:,} bytes")
        
        console.print(files_table)


def demo_file_selection(assistant):
    """Demo file selection preview."""
    console.print(Panel(
        "[bold blue]File Selection Demo[/bold blue]",
        border_style="blue"
    ))
    
    sample_questions = [
        "How does the configuration system work?",
        "What are the main components of this project?",
        "How is error handling implemented?",
        "What testing framework is used?",
    ]
    
    console.print("\n[bold]Sample questions you can try:[/bold]")
    for i, q in enumerate(sample_questions, 1):
        console.print(f"  {i}. {q}")
    
    question = Prompt.ask("\nEnter a question to preview file selection", default=sample_questions[0])
    
    console.print(f"\n[bold]🔍 Analyzing question:[/bold] {question}")
    
    try:
        preview = assistant.preview_file_selection(question)
        
        console.print(f"\n[bold green]✅ Selected Files ({len(preview['valid_files'])}):[/bold green]")
        for file_path in preview['valid_files']:
            console.print(f"  📄 {file_path}")
        
        if preview['invalid_files']:
            console.print(f"\n[bold red]❌ Invalid Files ({len(preview['invalid_files'])}):[/bold red]")
            for file_info in preview['invalid_files']:
                console.print(f"  ⚠️  {file_info}")
        
        console.print(f"\n[bold yellow]🤔 AI Reasoning:[/bold yellow]")
        console.print(preview['reasoning'])
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


def demo_question_answering(assistant):
    """Demo question answering."""
    console.print(Panel(
        "[bold blue]Question Answering Demo[/bold blue]",
        border_style="blue"
    ))
    
    sample_questions = [
        "What is the main purpose of this project?",
        "How is the project structured?",
        "What dependencies does this project have?",
        "Are there any configuration files?",
    ]
    
    console.print("\n[bold]Sample questions:[/bold]")
    for i, q in enumerate(sample_questions, 1):
        console.print(f"  {i}. {q}")
    
    question = Prompt.ask("\nEnter your question", default=sample_questions[0])
    
    console.print(f"\n[bold]🤖 Processing question:[/bold] {question}")
    
    try:
        answer = assistant.ask(question)
        
        console.print(Panel(
            answer,
            title="💡 Answer",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


def main():
    """Main demo function."""
    console.print(Panel(
        "[bold blue]Welcome to Repox Demo![/bold blue]\n\n"
        "This demo will show you how to use Repox to analyze and ask questions about your codebase.\n\n"
        "Repox uses AI to intelligently select relevant files and provide context-aware answers.",
        title="🤖 Repox Demo",
        border_style="blue"
    ))
    
    # Check environment
    if not check_environment():
        return
    
    # Show configuration
    console.print("\n")
    show_configuration()
    
    # Get repository path
    repo_path = Prompt.ask("\nEnter repository path", default=".")
    
    try:
        # Initialize assistant
        console.print(f"\n[bold]🚀 Initializing Repox for:[/bold] {Path(repo_path).resolve()}")
        
        config = RepoxConfig().get_effective_config()
        config.verbose = True  # Enable verbose mode for demo
        
        assistant = RepoxAssistant(repo_path, config)
        
        console.print("[bold green]✅ Repox initialized successfully![/bold green]")
        
        # Demo menu
        while True:
            console.print("\n" + "="*60)
            console.print("[bold]Choose a demo:[/bold]")
            console.print("1. Repository Analysis")
            console.print("2. File Selection Preview")
            console.print("3. Question Answering")
            console.print("4. Exit")
            
            choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4"], default="1")
            
            if choice == "1":
                demo_repository_analysis(assistant)
            elif choice == "2":
                demo_file_selection(assistant)
            elif choice == "3":
                demo_question_answering(assistant)
            elif choice == "4":
                console.print("[bold green]👋 Thanks for trying Repox![/bold green]")
                break
    
    except Exception as e:
        console.print(f"[bold red]Error initializing Repox:[/bold red] {e}")


if __name__ == "__main__":
    main()