"""graphrag-demo: Knowledge graph RAG with Gemini."""

import typer
from rich.panel import Panel
from rich.table import Table

from src.utils import (
    RAW_DIR,
    INPUT_DIR,
    OUTPUT_DIR,
    SUPPORTED_EXTENSIONS,
    console,
    ensure_directories,
    ensure_api_key,
    load_graphrag_config,
    check_index_exists,
    print_answer,
    print_error,
)
from src.ingest import ingest as run_ingest
from src.query import ask as run_ask

app = typer.Typer(
    name="graphrag-demo",
    help="Demo de Knowledge Graph RAG con Gemini.",
    add_completion=False,
)


@app.command()
def ingest():
    """Convierte documentos y ejecuta la indexación de GraphRAG."""
    ensure_directories()
    ensure_api_key()

    raw_files = [
        f for f in RAW_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not raw_files:
        console.print(
            Panel(
                "[yellow]No se encontraron documentos.[/yellow]\n\n"
                "Coloca tus archivos (PDF, DOCX, MD, TXT) en:\n"
                f"  [bold]{RAW_DIR}[/bold]",
                title="Para empezar",
                border_style="yellow",
            )
        )
        raise typer.Exit(0)

    console.print(f"[blue]Encontrados {len(raw_files)} documentos para procesar[/blue]")
    config = load_graphrag_config()
    run_ingest(RAW_DIR, INPUT_DIR, config)


@app.command()
def ask(
    query: str = typer.Argument(..., help="La pregunta a realizar"),
    local: bool = typer.Option(
        False, "--local", "-l", help="Usar búsqueda local en vez de global"
    ),
    community_level: int = typer.Option(
        2, "--level", "-L", help="Nivel de comunidad para la búsqueda"
    ),
):
    """Hace una pregunta al knowledge graph."""
    ensure_api_key()

    if not check_index_exists():
        print_error("No se encontró un índice. Ejecuta 'python main.py ingest' primero.")
        raise typer.Exit(1)

    config = load_graphrag_config()
    search_type = "local" if local else "global"

    with console.status(f"[bold blue]Ejecutando búsqueda {search_type}...[/bold blue]"):
        try:
            response, context = run_ask(
                config, OUTPUT_DIR, query, local, community_level
            )
        except FileNotFoundError as e:
            print_error(str(e))
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Error en la búsqueda: {e}")
            raise typer.Exit(1)

    print_answer(response, query, search_type)


@app.command()
def status():
    """Muestra el estado de la indexación."""
    ensure_directories()

    table = Table(title="Estado de GraphRAG")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green")

    raw_count = len([f for f in RAW_DIR.iterdir() if f.is_file()])
    table.add_row("Documentos en raw/", str(raw_count))

    txt_count = len(list(INPUT_DIR.glob("*.txt")))
    table.add_row("Archivos de texto", str(txt_count))

    entities_path = OUTPUT_DIR / "entities.parquet"
    if entities_path.exists():
        import pandas as pd
        from datetime import datetime

        mtime = datetime.fromtimestamp(entities_path.stat().st_mtime)
        table.add_row("Última indexación", mtime.strftime("%Y-%m-%d %H:%M:%S"))

        entities_df = pd.read_parquet(entities_path)
        table.add_row("Entidades", str(len(entities_df)))

        rel_path = OUTPUT_DIR / "relationships.parquet"
        if rel_path.exists():
            table.add_row("Relaciones", str(len(pd.read_parquet(rel_path))))

        comm_path = OUTPUT_DIR / "communities.parquet"
        if comm_path.exists():
            table.add_row("Comunidades", str(len(pd.read_parquet(comm_path))))
    else:
        table.add_row("Estado del índice", "[red]No indexado[/red]")

    console.print(table)


@app.command()
def graph(
    output: str = typer.Option(
        None, "--output", "-o", help="Archivo de salida (.mmd)"
    ),
):
    """Genera un diagrama Mermaid del knowledge graph."""
    if not check_index_exists():
        print_error("No se encontró un índice. Ejecuta 'python main.py ingest' primero.")
        raise typer.Exit(1)

    import pandas as pd
    from pathlib import Path

    entities = pd.read_parquet(OUTPUT_DIR / "entities.parquet")
    relationships = pd.read_parquet(OUTPUT_DIR / "relationships.parquet")

    type_styles = {
        "ORGANIZATION": ":::org",
        "GEO": ":::geo",
        "EVENT": ":::event",
        "PERSON": ":::person",
    }

    node_ids = {}
    lines = [
        "graph TD",
    ]

    for _, row in entities.iterrows():
        node_id = row["title"].replace(" ", "_").replace(".", "")
        node_ids[row["title"]] = node_id
        style = type_styles.get(row["type"], "")
        label = row["title"]
        lines.append(f'    {node_id}["{label}"]{style}')

    for _, row in relationships.iterrows():
        src = node_ids.get(row["source"], row["source"].replace(" ", "_"))
        tgt = node_ids.get(row["target"], row["target"].replace(" ", "_"))
        desc = row["description"]
        short = desc[:60] + "..." if len(desc) > 60 else desc
        short = short.replace('"', "'")
        lines.append(f'    {src} -->|"{short}"| {tgt}')

    lines.extend([
        "",
        "    classDef org fill:#4A90D9,stroke:#2C5F8A,color:#fff",
        "    classDef geo fill:#27AE60,stroke:#1E8449,color:#fff",
        "    classDef event fill:#E67E22,stroke:#D35400,color:#fff",
        "    classDef person fill:#8E44AD,stroke:#6C3483,color:#fff",
    ])

    mermaid = "\n".join(lines)

    out_path = Path(output) if output else OUTPUT_DIR / "graph.mmd"
    out_path.write_text(mermaid, encoding="utf-8")
    console.print(f"[green]Diagrama guardado en {out_path}[/green]")
    console.print(f"[dim]{len(entities)} entidades, {len(relationships)} relaciones[/dim]")
    console.print()
    console.print(Panel(mermaid, title="Mermaid", border_style="blue"))


@app.command()
def report(
    output: str = typer.Option(
        None, "--output", "-o", help="Archivo de salida (.md)"
    ),
):
    """Genera un reporte Markdown con todo lo que aprendio el RAG."""
    if not check_index_exists():
        print_error("No se encontró un índice. Ejecuta 'python main.py ingest' primero.")
        raise typer.Exit(1)

    import pandas as pd
    from pathlib import Path
    from datetime import datetime

    entities = pd.read_parquet(OUTPUT_DIR / "entities.parquet")
    relationships = pd.read_parquet(OUTPUT_DIR / "relationships.parquet")
    communities = pd.read_parquet(OUTPUT_DIR / "community_reports.parquet")

    lines = []

    # --- Header ---
    mtime = datetime.fromtimestamp((OUTPUT_DIR / "entities.parquet").stat().st_mtime)
    lines.append("# Reporte de Knowledge Graph")
    lines.append("")
    lines.append(f"> Generado: {mtime.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"> Entidades: {len(entities)} | Relaciones: {len(relationships)} | Comunidades: {len(communities)}")
    lines.append("")

    # --- Community Reports (main insights) ---
    for _, comm in communities.iterrows():
        lines.append(f"## {comm['title']}")
        lines.append("")
        lines.append(comm["summary"])
        lines.append("")

        if comm["findings"] is not None:
            for finding in comm["findings"]:
                lines.append(f"### {finding['summary']}")
                lines.append("")
                lines.append(finding["explanation"])
                lines.append("")

    # --- Entity Catalog ---
    lines.append("---")
    lines.append("")
    lines.append("## Catalogo de Entidades")
    lines.append("")
    lines.append("| Entidad | Tipo | Descripcion |")
    lines.append("|---------|------|-------------|")
    for _, e in entities.sort_values("type").iterrows():
        desc = e["description"].replace("\n", " ")
        if len(desc) > 200:
            desc = desc[:200] + "..."
        lines.append(f"| **{e['title']}** | {e['type']} | {desc} |")
    lines.append("")

    # --- Relationship Table ---
    lines.append("## Relaciones")
    lines.append("")
    lines.append("| Origen | Destino | Descripcion | Peso |")
    lines.append("|--------|---------|-------------|------|")
    for _, r in relationships.sort_values("weight", ascending=False).iterrows():
        desc = r["description"].replace("\n", " ")
        if len(desc) > 120:
            desc = desc[:120] + "..."
        lines.append(f"| {r['source']} | {r['target']} | {desc} | {r['weight']:.1f} |")
    lines.append("")

    # --- Mermaid diagram inline ---
    lines.append("## Grafo de Conocimiento")
    lines.append("")
    mmd_path = OUTPUT_DIR / "graph.mmd"
    if mmd_path.exists():
        lines.append("```mermaid")
        lines.append(mmd_path.read_text(encoding="utf-8").strip())
        lines.append("```")
    else:
        lines.append("*Ejecuta `python main.py graph` para generar el diagrama.*")
    lines.append("")

    md = "\n".join(lines)

    out_path = Path(output) if output else OUTPUT_DIR / "report.md"
    out_path.write_text(md, encoding="utf-8")
    console.print(f"[green]Reporte guardado en {out_path}[/green]")
    console.print(f"[dim]{len(communities)} comunidades, {len(entities)} entidades, {len(relationships)} relaciones[/dim]")


if __name__ == "__main__":
    app()
