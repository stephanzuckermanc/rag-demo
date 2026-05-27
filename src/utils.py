"""Shared utilities for graphrag-demo."""

import os
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
INPUT_DIR = PROJECT_ROOT / "data" / "input"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
CONFIG_DIR = PROJECT_ROOT / "config"
ENV_FILE = CONFIG_DIR / ".env"
SETTINGS_FILE = CONFIG_DIR / "settings.yaml"

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".md", ".txt"}

console = Console()


def ensure_directories() -> None:
    """Create data/raw/, data/input/, output/ if they don't exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def ensure_api_key() -> None:
    """Load .env; if GEMINI_API_KEY is missing, prompt interactively and save."""
    load_dotenv(ENV_FILE)
    if os.getenv("GEMINI_API_KEY"):
        return

    console.print(
        Panel(
            "[yellow]No se encontró GEMINI_API_KEY.[/yellow]\n\n"
            "Obtén una key gratuita en: [link]https://aistudio.google.com[/link]",
            title="API Key",
            border_style="yellow",
        )
    )
    key = Prompt.ask("[bold]Ingresa tu Gemini API key[/bold]")
    if not key.strip():
        console.print("[red]La API key no puede estar vacía.[/red]")
        raise SystemExit(1)

    ENV_FILE.write_text(f"GEMINI_API_KEY={key.strip()}\n")
    os.environ["GEMINI_API_KEY"] = key.strip()
    console.print("[green]API key guardada en .env[/green]")


def load_graphrag_config():
    """Load GraphRAG config from settings.yaml. Returns a GraphRagConfig."""
    from graphrag.config.load_config import load_config

    if not SETTINGS_FILE.exists():
        print_error(f"No se encontró {SETTINGS_FILE}. Verifica la instalación.")
        raise SystemExit(1)

    return load_config(CONFIG_DIR)


def check_index_exists() -> bool:
    """Return True if output/entities.parquet exists (indexing has been run)."""
    return (OUTPUT_DIR / "entities.parquet").exists()


def print_answer(response: str, query: str, search_type: str) -> None:
    """Display a search response in a Rich panel."""
    label = "Global" if search_type == "global" else "Local"
    console.print(
        Panel(
            response,
            title=f"[bold green]{label} Search[/bold green]",
            subtitle=f"[dim]Q: {query}[/dim]",
            border_style="green",
            padding=(1, 2),
        )
    )


def print_error(message: str) -> None:
    """Display an error message with Rich formatting."""
    console.print(f"[bold red]Error:[/bold red] {message}")
