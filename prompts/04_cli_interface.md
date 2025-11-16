# Prompt 04: CLI Interface Implementation

## Metadata
- **Phase**: Foundation
- **Priority**: High
- **Estimated Time**: 3-4 hours
- **Dependencies**: Prompts 01, 02, 03
- **Files to Create**: `src/cli/main.py`, `src/cli/commands/`, `src/cli/display.py`

---

# GITHUB COPILOT PROMPT: CLI INTERFACE IMPLEMENTATION

## Context

You are implementing a comprehensive command-line interface for MediaForge using Typer and Rich libraries. The CLI must provide:
- Intuitive commands for all core operations
- Beautiful, colorful output with progress bars
- Interactive prompts when needed
- Comprehensive help documentation
- Error handling with helpful messages

## Technical Requirements

### CLI Commands Structure

```
mediaforge
├── scan         # Scan directories for media
├── search       # Search media library
├── info         # Display media item info
├── stats        # Show library statistics
├── tag          # Manage tags
├── collection   # Manage collections
├── export       # Export metadata
├── import       # Import metadata
├── verify       # Verify file integrity
└── config       # Configuration management
```

### Implementation

Create `src/cli/main.py`:

```python
import typer
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.core.config import settings
from src.core.database import Database
from src.core.scanner import MediaScanner
from src.core.metadata_extractor import MetadataExtractor

app = typer.Typer(
    name="mediaforge",
    help="MediaForge - Forge Your Perfect Media Collection",
    add_completion=False
)
console = Console()

# Initialize database
db = Database(settings.database_url)

@app.command()
async def scan(
    path: Path = typer.Argument(..., help="Directory to scan"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r/-R", help="Scan subdirectories"),
    include_hidden: bool = typer.Option(False, "--hidden", "-h", help="Include hidden files"),
    incremental: bool = typer.Option(True, "--incremental/--full", "-i/-f", help="Skip already scanned files"),
    extract_metadata: bool = typer.Option(True, "--metadata/--no-metadata", "-m/-M", help="Extract metadata after scanning"),
):
    """
    Scan a directory for media files and add them to the library.
    
    Example:
        mediaforge scan /media/movies --recursive --metadata
    """
    console.print(f"[bold blue]✨ Starting scan of:[/bold blue] {path}")
    
    if not path.exists():
        console.print(f"[bold red]❌ Error:[/bold red] Directory not found: {path}")
        raise typer.Exit(1)
    
    # Initialize scanner
    scanner = MediaScanner(db)
    
    # Perform scan with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Scanning files...", total=None)
        
        result = await scanner.scan_directory(
            path,
            recursive=recursive,
            include_hidden=include_hidden,
            incremental=incremental
        )
        
        progress.update(task, completed=True)
    
    # Display results
    display_scan_results(result)
    
    # Extract metadata if requested
    if extract_metadata and result.new_files > 0:
        console.print("\n[bold blue]📊 Extracting metadata...[/bold blue]")
        # TODO: Implement metadata extraction

@app.command()
async def search(
    query: str = typer.Argument(..., help="Search query"),
    media_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by media type (video/audio/image)"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results to show"),
):
    """
    Search your media library.
    
    Example:
        mediaforge search "vacation" --type video --limit 10
    """
    console.print(f"[bold blue]🔍 Searching for:[/bold blue] {query}")
    
    # TODO: Implement search (Phase 2)
    console.print("[yellow]Search functionality coming in Phase 2![/yellow]")

@app.command()
async def info(
    file_path: Path = typer.Argument(..., help="Path to media file or ID")
):
    """
    Display detailed information about a media item.
    
    Example:
        mediaforge info /media/movies/movie.mp4
    """
    console.print(f"[bold blue]📜 Getting info for:[/bold blue] {file_path}")
    
    # TODO: Implement info display
    pass

@app.command()
async def stats():
    """
    Display library statistics.
    
    Example:
        mediaforge stats
    """
    console.print("[bold blue]📊 MediaForge Library Statistics[/bold blue]\n")
    
    # TODO: Implement statistics
    table = Table(title="Library Overview")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Files", "0")
    table.add_row("Total Size", "0 GB")
    table.add_row("Videos", "0")
    table.add_row("Audio Files", "0")
    table.add_row("Images", "0")
    
    console.print(table)

@app.command()
async def verify():
    """
    Verify integrity of all media files.
    
    Example:
        mediaforge verify
    """
    console.print("[bold blue]✅ Verifying file integrity...[/bold blue]")
    
    # TODO: Implement verification
    console.print("[yellow]Verification functionality coming soon![/yellow]")

def display_scan_results(result):
    """Display scan results in a beautiful table"""
    table = Table(title="🎯 Scan Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Files Scanned", str(result.total_files))
    table.add_row("New Files", f"[bold green]{result.new_files}[/bold green]")
    table.add_row("Updated Files", str(result.updated_files))
    table.add_row("Skipped Files", str(result.skipped_files))
    table.add_row("Errors", f"[bold red]{result.error_files}[/bold red]" if result.error_files > 0 else "0")
    table.add_row("Total Size", format_file_size(result.total_size))
    table.add_row("Duration", f"{result.scan_duration:.2f}s")
    
    console.print(table)
    
    if result.errors:
        console.print("\n[bold red]⚠️ Errors:[/bold red]")
        for error in result.errors[:10]:  # Show first 10 errors
            console.print(f"  [red]•[/red] {error}")
        if len(result.errors) > 10:
            console.print(f"  [dim]... and {len(result.errors) - 10} more errors[/dim]")

def format_file_size(size_bytes: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

if __name__ == "__main__":
    app()
```

### Tag Management Commands

Create `src/cli/commands/tag.py`:

```python
import typer
from rich.console import Console
from rich.table import Table

tag_app = typer.Typer(help="Manage tags")
console = Console()

@tag_app.command("list")
async def list_tags():
    """List all tags"""
    # TODO: Implement
    pass

@tag_app.command("add")
async def add_tag(
    name: str = typer.Argument(..., help="Tag name"),
    description: str = typer.Option("", "--description", "-d", help="Tag description"),
    color: str = typer.Option("#3498db", "--color", "-c", help="Tag color (hex)")
):
    """Add a new tag"""
    # TODO: Implement
    pass

@tag_app.command("apply")
async def apply_tag(
    tag: str = typer.Argument(..., help="Tag name"),
    file_path: str = typer.Argument(..., help="File path or ID")
):
    """Apply tag to a media item"""
    # TODO: Implement
    pass
```

### Collection Management

Create `src/cli/commands/collection.py`:

```python
import typer

collection_app = typer.Typer(help="Manage collections")

@collection_app.command("create")
async def create_collection(
    name: str = typer.Argument(..., help="Collection name"),
    description: str = typer.Option("", "--description", "-d")
):
    """Create a new collection"""
    # TODO: Implement
    pass

@collection_app.command("add")
async def add_to_collection(
    collection: str = typer.Argument(..., help="Collection name"),
    file_path: str = typer.Argument(..., help="File path or ID")
):
    """Add media item to collection"""
    # TODO: Implement
    pass

@collection_app.command("list")
async def list_collections():
    """List all collections"""
    # TODO: Implement
    pass
```

### Register Subcommands

In `src/cli/main.py`, add:

```python
from src.cli.commands.tag import tag_app
from src.cli.commands.collection import collection_app

app.add_typer(tag_app, name="tag")
app.add_typer(collection_app, name="collection")
```

## Testing Requirements

Create `tests/unit/test_cli.py`:

1. **Test Command Parsing**
2. **Test Output Formatting**
3. **Test Error Handling**
4. **Test Progress Display**

## Success Criteria

- [ ] All commands implemented
- [ ] Beautiful Rich output
- [ ] Progress bars work
- [ ] Error messages helpful
- [ ] Help text comprehensive
- [ ] Commands intuitive

---

**GENERATE COMPLETE, PRODUCTION-READY CODE FOR ALL REQUIREMENTS ABOVE**