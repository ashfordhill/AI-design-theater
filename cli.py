"""Command-line interface for AI Design Theater."""

import asyncio
import os
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional

from src.main import AIDesignTheater
from web_viewer import ConversationWebViewer
from src.idea_generation.topic_generator import TopicGenerator
from src.storage.project_storage import ProjectStorage
from src.config import config

app = typer.Typer(help="AI Design Theater - Where AI personalities collaborate on software design")
console = Console()


@app.command()
def run(
    topic: str = typer.Argument(..., help="The design topic or problem to discuss"),
    context: Optional[str] = typer.Option(None, "--context", "-c", help="Additional context for the discussion"),
    max_turns: Optional[int] = typer.Option(None, "--max-turns", "-t", help="Maximum number of conversation turns"),
    max_duration: Optional[int] = typer.Option(None, "--max-duration", "-d", help="Maximum duration in minutes"),
    tone: Optional[str] = typer.Option(None, "--tone", help="Stylistic tone (e.g., casual, formal)"),
    debate_intensity: Optional[int] = typer.Option(None, "--debate-intensity", help="0-10: Higher -> more disagreement & challenge (env DEBATE_INTENSITY default)"),
    diagram_detail: Optional[int] = typer.Option(None, "--diagram-detail", help="1-10: Higher -> richer component diagrams (env DIAGRAM_DETAIL_LEVEL default)"),
):
    """Run a design conversation between AI personalities."""
    
    async def run_session():
        theater = AIDesignTheater()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running design session...", total=None)
            
            try:
                project_dir = await theater.run_design_session(
                    topic=topic,
                    context=context,
                    max_turns=max_turns,
                    max_duration_minutes=max_duration,
                    tone=tone,
                    debate_intensity=debate_intensity,
                    diagram_detail_level=diagram_detail
                )
                
                progress.update(task, description="✅ Session complete!")
                
                console.print(Panel(
                    f"[green]Design session completed successfully![/green]\n\n"
                    f"[bold]Topic:[/bold] {topic}\n"
                    f"[bold]Project saved to:[/bold] {project_dir}\n\n"
                    f"Check the project directory for:\n"
                    f"• 📄 DESIGN.md - Design document\n"
                    f"• 💬 conversation.md - Full transcript\n"
                    f"• 📊 diagram.mmd - Mermaid diagram\n"
                    f"• 📋 session.json - Raw session data",
                    title="🎉 Success",
                    border_style="green"
                ))
                
            except Exception as e:
                progress.update(task, description="❌ Session failed!")
                console.print(Panel(
                    f"[red]Error running design session:[/red]\n{str(e)}",
                    title="❌ Error",
                    border_style="red"
                ))
                raise typer.Exit(1)
    
    asyncio.run(run_session())


@app.command()
def list():
    """List all saved design projects."""
    theater = AIDesignTheater()
    projects = theater.list_projects()
    
    if not projects:
        console.print("No design projects found.")
        return
    
    table = Table(title="🎭 AI Design Theater Projects")
    table.add_column("Name", style="cyan")
    table.add_column("Topic", style="green")
    table.add_column("Created", style="yellow")
    table.add_column("Path", style="dim")
    
    for project in projects:
        table.add_row(
            project['name'],
            project['topic'],
            project['created'][:19] if len(project['created']) > 19 else project['created'],
            project['path']
        )
    
    console.print(table)


@app.command()
def validate():
    """Validate the application setup and API connections."""
    
    async def check_setup():
        theater = AIDesignTheater()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Validating setup...", total=None)
            
            results = await theater.validate_setup()
            progress.update(task, description="✅ Validation complete!")
        
        # Display results
        table = Table(title="🔍 Setup Validation Results")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        
        status_icon = lambda x: "✅" if x else "❌"
        
        table.add_row("API Keys Configured", f"{status_icon(results['api_keys'])} {'Yes' if results['api_keys'] else 'No'}")
        table.add_row("OpenAI Connection", f"{status_icon(results['openai_connection'])} {'Working' if results['openai_connection'] else 'Failed'}")
        table.add_row("Anthropic Connection", f"{status_icon(results['anthropic_connection'])} {'Working' if results['anthropic_connection'] else 'Failed'}")
        table.add_row("Projects Directory", f"{status_icon(results['projects_dir'])} {'Ready' if results['projects_dir'] else 'Missing'}")
        
        console.print(table)
        
        if not results['api_keys']:
            console.print(Panel(
                "[yellow]⚠️  No API keys configured![/yellow]\n\n"
                "Please set at least one of the following environment variables:\n"
                "• OPENAI_API_KEY\n"
                "• ANTHROPIC_API_KEY\n\n"
                "You can also create a .env file in the project root.",
                title="Configuration Required",
                border_style="yellow"
            ))
    
    asyncio.run(check_setup())


@app.command()
def web():
    """Generate HTML viewer for all design projects."""
    viewer = ConversationWebViewer()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating web viewer...", total=None)
        
        try:
            viewer.generate_all_html_files()
            progress.update(task, description="✅ Web viewer generated!")
            
            console.print(Panel(
                "[green]Web viewer generated successfully![/green]\n\n"
                "📁 Files created in 'web_output' directory\n"
                "🌐 Open 'web_output/index.html' in your browser\n\n"
                "The web viewer includes:\n"
                "• 📋 Project index with all design sessions\n"
                "• 💬 Full conversation transcripts\n"
                "• 📊 Interactive Mermaid diagrams\n"
                "• 📄 Formatted design documents",
                title="🌐 Web Viewer Ready",
                border_style="green"
            ))
            
        except Exception as e:
            progress.update(task, description="❌ Generation failed!")
            console.print(Panel(
                f"[red]Error generating web viewer:[/red]\n{str(e)}",
                title="❌ Error",
                border_style="red"
            ))
            raise typer.Exit(1)


@app.command()
def example():
    """Show example usage and topics."""
    console.print(Panel(
        "[bold cyan]AI Design Theater Examples[/bold cyan]\n\n"
        "[bold]Basic Usage:[/bold]\n"
        "python cli.py run \"Design a task management app\"\n\n"
        "[bold]With Context:[/bold]\n"
        "python cli.py run \"Design a microservices architecture\" --context \"For a e-commerce platform with 1M users\"\n\n"
        "[bold]With Limits:[/bold]\n"
        "python cli.py run \"Design a caching strategy\" --max-turns 15 --max-duration 20\n\n"
        "[bold]Other Commands:[/bold]\n"
        "python cli.py list          # List all projects\n"
        "python cli.py validate      # Check setup\n"
        "python cli.py web          # Generate web viewer\n"
        "python cli.py readme --all  # Regenerate all READMEs\n\n"
        "[bold]Example Topics:[/bold]\n"
        "• \"Design a real-time chat application\"\n"
        "• \"Create a CI/CD pipeline for a Python web app\"\n"
        "• \"Design a scalable image processing service\"\n"
        "• \"Plan a database migration strategy\"\n"
        "• \"Design an API rate limiting system\"\n"
        "• \"Create a monitoring and alerting solution\"",
        title="💡 Examples & Ideas",
        border_style="blue"
    ))


@app.command()
def random(keywords: Optional[str] = typer.Option(None, "--keywords", help="Comma separated keywords to bias topic selection (overrides IDEA_KEYWORDS for this run)")):
    """Run a design session with a random predefined topic (keyword-biased if provided)."""
    tg = TopicGenerator()
    # Temporary override of config keywords if user passed option
    if keywords:
        os.environ["IDEA_KEYWORDS"] = keywords
    topic_data = tg.get_random_topic()
    topic = topic_data['topic']
    context = topic_data.get('context')
    console.print(f"[cyan]Random Topic:[/cyan] {topic}\n[dim]{context}[/dim]")
    asyncio.run(AIDesignTheater().run_design_session(topic=topic, context=context))


@app.command()
def daily_topic(keywords: Optional[str] = typer.Option(None, "--keywords", help="Comma separated keywords to bias today's topic")):
    """Run a design session with the deterministic day-of-week topic (keyword-biased if provided)."""
    tg = TopicGenerator()
    if keywords:
        os.environ["IDEA_KEYWORDS"] = keywords
    topic_data = tg.get_daily_topic()
    topic = topic_data['topic']
    context = topic_data.get('context')
    console.print(f"[cyan]Daily Topic:[/cyan] {topic}\n[dim]{context}[/dim]")
    asyncio.run(AIDesignTheater().run_design_session(topic=topic, context=context))


@app.command()
def readme(
    project_path: Optional[str] = typer.Argument(None, help="Path to specific project directory"),
    all_projects: bool = typer.Option(False, "--all", "-a", help="Regenerate READMEs for all projects")
):
    """Regenerate README.md files with conversation logs and diagrams."""
    storage = ProjectStorage()
    
    if all_projects:
        console.print("[cyan]Regenerating READMEs for all projects...[/cyan]")
        projects = storage.list_projects()
        
        success_count = 0
        for project in projects:
            if storage.regenerate_readme(project['path']):
                console.print(f"✅ {project['name']}")
                success_count += 1
            else:
                console.print(f"❌ {project['name']} (failed)")
        
        console.print(f"\n[green]Successfully regenerated {success_count}/{len(projects)} READMEs[/green]")
    
    elif project_path:
        console.print(f"[cyan]Regenerating README for {project_path}...[/cyan]")
        if storage.regenerate_readme(project_path):
            console.print("✅ README generated successfully!")
        else:
            console.print("❌ Failed to generate README")
    
    else:
        # Show available projects
        projects = storage.list_projects()
        if not projects:
            console.print("[yellow]No projects found.[/yellow]")
            return
        
        console.print("[cyan]Available projects:[/cyan]")
        table = Table()
        table.add_column("Name", style="cyan")
        table.add_column("Topic", style="white")
        table.add_column("Path", style="dim")
        
        for project in projects:
            table.add_row(project['name'], project['topic'], project['path'])
        
        console.print(table)
        console.print("\n[dim]Use: python cli.py readme <project_path> or python cli.py readme --all[/dim]")


if __name__ == "__main__":
    app()