"""
Display utilities for MediaForge CLI (Rich-based)
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Any, Dict

console = Console()

def display_scan_results(result):
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
    if getattr(result, "errors", None):
        console.print("\n[bold red]⚠️ Errors:[/bold red]")
        for error in result.errors[:10]:
            console.print(f"  [red]•[/red] {error}")
        if len(result.errors) > 10:
            console.print(f"  [dim]... and {len(result.errors) - 10} more errors[/dim]")

def format_file_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def display_error(message: str):
    console.print(Panel(Text(message, style="bold red"), title="[red]Error[/red]", style="red"))

def display_success(message: str):
    console.print(Panel(Text(message, style="bold green"), title="[green]Success[/green]", style="green"))

def display_info(message: str):
    console.print(Panel(Text(message, style="bold blue"), title="[blue]Info[/blue]", style="blue"))

def display_stats(stats: Dict[str, Any]):
    table = Table(title="Library Overview")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in stats.items():
        table.add_row(str(k), str(v))
    console.print(table)

def display_table(title: str, columns: list, rows: list):
    table = Table(title=title)
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    console.print(table)
