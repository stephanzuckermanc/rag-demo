"""Automated demo: runs a series of questions against the indexed report."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from src.utils import ensure_api_key, load_graphrag_config, check_index_exists, OUTPUT_DIR
from src.query import ask

console = Console()

QUESTIONS = [
    ("Resumen general del reporte de Chevrolet México en mayo 2026", "global"),
    ("Qué plataforma tiene mejor engagement y por qué?", "local"),
    ("Cuáles son las métricas de TikTok vs Facebook?", "local"),
    ("Qué tipo de contenido genera más interacciones?", "global"),
    ("Cuál es el alcance orgánico total sumando todas las plataformas?", "local"),
    ("Qué rol juega Instagram Stories dentro de la estrategia?", "local"),
    ("Qué oportunidades de mejora se identifican en el reporte?", "global"),
]


def main():
    ensure_api_key()

    if not check_index_exists():
        console.print("[red]No hay índice. Ejecuta 'python main.py ingest' primero.[/red]")
        raise SystemExit(1)

    config = load_graphrag_config()

    console.print(Panel(
        f"[bold]Demo automatizado — {len(QUESTIONS)} preguntas[/bold]\n"
        "Cada pregunta usa global o local search según convenga.",
        title="graphrag-demo",
        border_style="blue",
    ))

    for i, (question, mode) in enumerate(QUESTIONS, 1):
        console.print(Rule(f"[bold cyan]Pregunta {i}/{len(QUESTIONS)}[/bold cyan]"))
        console.print(f"[yellow]{question}[/yellow]")
        console.print(f"[dim]Modo: {mode} search[/dim]\n")

        start = time.time()
        local = mode == "local"

        with console.status("[blue]Pensando...[/blue]"):
            response, _ = ask(config, OUTPUT_DIR, question, local=local)

        elapsed = time.time() - start

        console.print(Panel(
            response,
            title=f"[green]{mode.title()} Search[/green]",
            subtitle=f"[dim]{elapsed:.1f}s[/dim]",
            border_style="green",
            padding=(1, 2),
        ))
        console.print()


if __name__ == "__main__":
    main()
