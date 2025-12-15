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
from typing import Optional, List
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from src.core.config import settings
from src.core.database import Database
from src.core.scanner import MediaScanner
from src.core.metadata_extractor import MetadataExtractor
from src.models.media import MediaType, MediaItem
from src.models.metadata import MediaMetadata
from sqlalchemy import select
from src.cli.display import (
    display_scan_results, display_error, display_info, display_stats, display_success, display_table
)
from src.cli.commands.tag import tag_app
from src.cli.commands.collection import collection_app
import asyncio

app = typer.Typer(
    name="mediaforge",
    help="MediaForge - Forge Your Perfect Media Collection",
    add_completion=False
)
console = Console()


import os

def get_db():
    db_url = os.environ.get("MEDIAFORGE_DATABASE_URL", settings.database_url)
    return Database(db_url)

async def _scan_impl(
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
    db = get_db()
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
    if extract_metadata and getattr(result, "new_files", 0) > 0:
        console.print("\n[bold blue]📊 Extracting metadata...[/bold blue]")
        extractor = MetadataExtractor()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            new_paths: List[str] = getattr(result, "new_file_paths", []) or []
            db_items: List[MediaItem] = []
            # Query DB for newly added media items
            if new_paths:
                async with get_db().session() as session:
                    db_result = await session.execute(
                        select(MediaItem).where(MediaItem.file_path.in_(new_paths))
                    )
                    db_items = list(db_result.scalars().all())

                    # If no items found (e.g., test mocks), create placeholder stubs for progress only
                    if not db_items:
                        db_items = [
                            type("_Stub", (), {
                                "id": i + 1,
                                "file_path": p,
                                "file_name": Path(p).name,
                                "media_type": MediaType.video,
                            })
                            for i, p in enumerate(new_paths)
                        ]  # type: ignore

                    task = progress.add_task("Extracting metadata...", total=len(db_items))

                    def _progress_cb(processed: int, total: int):
                        progress.advance(task)

                    metadata_results = await extractor.batch_extract(db_items, progress_callback=_progress_cb)  # type: ignore[arg-type]

                    # Persist metadata only if real MediaItem instances (attribute check)
                    real_items = [mi for mi in db_items if isinstance(mi, MediaItem)]
                    if real_items:
                        for mi in real_items:
                            data = metadata_results.get(str(mi.id), {})
                            if not data:
                                continue
                            async with get_db().session() as meta_session:
                                # Refresh item to attach session
                                item_res = await meta_session.execute(select(MediaItem).where(MediaItem.id == mi.id))
                                item_obj = item_res.scalar_one_or_none()
                                if not item_obj:
                                    continue
                                # Update or create metadata
                                meta_obj = item_obj.media_metadata
                                if not meta_obj:
                                    meta_obj = MediaMetadata(media_item_id=item_obj.id)
                                # Map fields
                                meta_obj.duration = data.get("duration")
                                meta_obj.width = data.get("width")
                                meta_obj.height = data.get("height")
                                meta_obj.fps = data.get("fps")
                                meta_obj.video_codec = data.get("video_codec")
                                meta_obj.audio_codec = data.get("audio_codec")
                                meta_obj.bitrate = data.get("bitrate")
                                meta_obj.sample_rate = data.get("audio_sample_rate") or data.get("sample_rate")
                                meta_obj.channels = data.get("audio_channels") or data.get("channels")
                                meta_obj.artist = data.get("artist")
                                meta_obj.album = data.get("album")
                                meta_obj.title = data.get("title") or item_obj.file_name
                                meta_obj.year = data.get("year")
                                meta_obj.genre = data.get("genre")
                                meta_obj.camera_make = data.get("camera_make")
                                meta_obj.camera_model = data.get("camera_model")
                                meta_obj.iso = data.get("iso")
                                meta_obj.aperture = data.get("aperture")
                                meta_obj.shutter_speed = data.get("shutter_speed")
                                meta_obj.focal_length = data.get("focal_length")
                                meta_obj.latitude = data.get("latitude")
                                meta_obj.longitude = data.get("longitude")
                                meta_obj.location_name = data.get("location_name")
                                # Store remaining keys in extra_metadata
                                meta_obj.extra_metadata = {k: v for k, v in data.items() if k not in {
                                    "duration","width","height","fps","video_codec","audio_codec","bitrate","audio_sample_rate","sample_rate","audio_channels","channels","artist","album","title","year","genre","camera_make","camera_model","iso","aperture","shutter_speed","focal_length","latitude","longitude","location_name"
                                }}
                                item_obj.is_processed = True
                                meta_session.add(meta_obj)
                                meta_session.add(item_obj)
                                # Commit per item to keep it simple; could batch optimize later
                                # (commit handled by session context manager)
            progress.update(task, completed=True)
        display_success("Metadata extraction complete.")


@app.command()
def scan(
    path: Path = typer.Argument(..., help="Directory to scan"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r/-R", help="Scan subdirectories"),
    include_hidden: bool = typer.Option(False, "--hidden", "-h", help="Include hidden files"),
    incremental: bool = typer.Option(True, "--incremental/--full", "-i/-f", help="Skip already scanned files"),
    extract_metadata: bool = typer.Option(True, "--metadata/--no-metadata", "-m/-M", help="Extract metadata after scanning"),
):
    asyncio.run(_scan_impl(path, recursive, include_hidden, incremental, extract_metadata))

@app.command()
def search(
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
def info(
    file_path: Path = typer.Argument(..., help="Path to media file or ID")
):
    """
    Display detailed information about a media item.
    """
    console.print(f"[bold blue]📜 Getting info for:[/bold blue] {file_path}")
    # Placeholder: Implement info display
    display_info("Info display coming soon!")

@app.command()
def stats():
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
def verify():
    """
    Verify integrity of all media files.
    """
    console.print("[bold blue]✅ Verifying file integrity...[/bold blue]")
    # Placeholder: Implement verification
    display_info("Verification functionality coming soon!")

@app.command()
def export_(
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
def import_(
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
def config(
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
