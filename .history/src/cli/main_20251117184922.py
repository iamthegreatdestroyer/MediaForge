"""
Copyright (c) 2025 [Your Name]. All Rights Reserved.

This file is part of DOPPELGANGER STUDIO.

DOPPELGANGER STUDIO is proprietary software with dual licensing:
- AGPLv3 for personal use
- Commercial license available

Patent Pending: AI-Driven Content Transformation System

Unauthorized copying, modification, or distribution is prohibited.
"""

import typer
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from src.core.config import settings
from src.core.database import Database
from src.core.scanner import MediaScanner
from src.core.metadata_extractor import MetadataExtractor
from src.cli.display import (
    display_scan_results, display_error, display_info, display_stats, display_success, display_table
)
from src.cli.commands.tag import tag_app
from src.cli.commands.collection import collection_app

app = typer.Typer(
    name="mediaforge",
    help="MediaForge - Forge Your Perfect Media Collection",
    add_completion=False
)
console = Console()

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
    """
    console.print(f"[bold blue]✨ Starting scan of:[/bold blue] {path}")
    if not path.exists():
        display_error(f"Directory not found: {path}")
        raise typer.Exit(1)
    scanner = MediaScanner(db)
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
    display_scan_results(result)
    if extract_metadata and result.new_files > 0:
        console.print("\n[bold blue]📊 Extracting metadata...[/bold blue]")
        extractor = MetadataExtractor(db)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Extracting metadata...", total=result.new_files)
            await extractor.extract_batch(result.new_file_paths, progress_callback=lambda: progress.advance(task))
            progress.update(task, completed=True)
        display_success("Metadata extraction complete.")

@app.command()
async def search(
    query: str = typer.Argument(..., help="Search query"),
    media_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by media type (video/audio/image)"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results to show"),
):
    """
    Search your media library.
    """
    console.print(f"[bold blue]🔍 Searching for:[/bold blue] {query}")
    # Placeholder: Implement search in Phase 2
    display_info("Search functionality coming in Phase 2!")

@app.command()
async def info(
    file_path: Path = typer.Argument(..., help="Path to media file or ID")
):
    """
    Display detailed information about a media item.
    """
    console.print(f"[bold blue]📜 Getting info for:[/bold blue] {file_path}")
    # Placeholder: Implement info display
    display_info("Info display coming soon!")

@app.command()
async def stats():
    """
    Display library statistics.
    """
    console.print("[bold blue]📊 MediaForge Library Statistics[/bold blue]\n")
    # Placeholder: Implement statistics
    display_stats({
        "Total Files": 0,
        "Total Size": "0 GB",
        "Videos": 0,
        "Audio Files": 0,
        "Images": 0
    })

@app.command()
async def verify():
    """
    Verify integrity of all media files.
    """
    console.print("[bold blue]✅ Verifying file integrity...[/bold blue]")
    # Placeholder: Implement verification
    display_info("Verification functionality coming soon!")

@app.command()
async def export_(
    output: Path = typer.Argument(..., help="Output file for exported metadata"),
    format: str = typer.Option("json", "--format", "-f", help="Export format (json/csv)"),
):
    """
    Export media metadata to a file.
    """
    console.print(f"[bold blue]📤 Exporting metadata to:[/bold blue] {output}")
    # Placeholder: Implement export
    display_info("Export functionality coming soon!")

@app.command()
async def import_(
    input_file: Path = typer.Argument(..., help="Input file for importing metadata"),
    format: str = typer.Option("json", "--format", "-f", help="Import format (json/csv)"),
):
    """
    Import media metadata from a file.
    """
    console.print(f"[bold blue]📥 Importing metadata from:[/bold blue] {input_file}")
    # Placeholder: Implement import
    display_info("Import functionality coming soon!")

@app.command()
async def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    set_key: Optional[str] = typer.Option(None, "--set", help="Set configuration key"),
    set_value: Optional[str] = typer.Option(None, "--value", help="Value for configuration key"),
):
    """
    Manage MediaForge configuration.
    """
    if show:
        display_info(f"Current config: {settings.dict()}")
    elif set_key and set_value:
        # Placeholder: Implement config set
        display_success(f"Set {set_key} = {set_value}")
    else:
        display_info("Use --show to display config or --set/--value to update.")

app.add_typer(tag_app, name="tag")
app.add_typer(collection_app, name="collection")

if __name__ == "__main__":
    app()
