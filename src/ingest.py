"""Document ingestion: conversion to plain text + GraphRAG indexing."""

import asyncio
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from src.utils import console, print_error, SUPPORTED_EXTENSIONS


def convert_pdf(source: Path) -> str:
    """Extract text from a PDF using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(source)
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def convert_docx(source: Path) -> str:
    """Extract text from a DOCX using python-docx."""
    from docx import Document

    doc = Document(source)
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


def convert_file(source: Path) -> str:
    """Convert a single file to plain text based on extension."""
    ext = source.suffix.lower()
    if ext == ".pdf":
        return convert_pdf(source)
    if ext in (".docx", ".doc"):
        return convert_docx(source)
    if ext in (".md", ".txt"):
        return source.read_text(encoding="utf-8")
    raise ValueError(f"Tipo de archivo no soportado: {ext}")


def convert_all_documents(raw_dir: Path, input_dir: Path) -> list[Path]:
    """
    Convert all supported docs from raw_dir to .txt in input_dir.
    Skips files whose .txt target is already newer than the source.
    Returns list of newly converted paths.
    """
    converted = []
    for source in sorted(raw_dir.iterdir()):
        if not source.is_file() or source.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        target = input_dir / (source.stem + ".txt")
        if target.exists() and target.stat().st_mtime >= source.stat().st_mtime:
            continue

        text = convert_file(source)
        if not text.strip():
            console.print(f"[yellow]Advertencia: {source.name} no produjo texto[/yellow]")
            continue

        target.write_text(text, encoding="utf-8")
        converted.append(target)

    return converted


async def run_indexing(config) -> list:
    """Run GraphRAG indexing pipeline. Returns list of PipelineRunResult."""
    import graphrag.api as api
    from graphrag.config.enums import IndexingMethod

    return await api.build_index(
        config=config,
        method=IndexingMethod.Standard,
        verbose=True,
    )


def ingest(raw_dir: Path, input_dir: Path, config) -> None:
    """
    Full ingestion pipeline:
    1. Convert documents from raw_dir → input_dir (.txt)
    2. Run GraphRAG indexing with Rich progress spinner
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        # --- Step 1: Document conversion ---
        task = progress.add_task("Convirtiendo documentos...", total=None)
        converted = convert_all_documents(raw_dir, input_dir)

        txt_count = len(list(input_dir.glob("*.txt")))
        if converted:
            progress.update(task, description=f"[green]Convertidos {len(converted)} documentos nuevos[/green] ({txt_count} total)")
        else:
            progress.update(task, description=f"[dim]Sin documentos nuevos que convertir[/dim] ({txt_count} listos)")

        if txt_count == 0:
            print_error("No hay archivos de texto después de la conversión. Agrega documentos a data/raw/")
            raise SystemExit(1)

        # --- Step 2: GraphRAG indexing ---
        progress.update(task, description="Ejecutando indexación GraphRAG (esto puede tomar varios minutos)...")

        results = asyncio.run(run_indexing(config))

        errors = [r for r in results if r.error]
        if errors:
            for r in errors:
                console.print(f"[red]Workflow {r.workflow} falló: {r.error}[/red]")
            raise SystemExit(1)

        progress.update(task, description="[bold green]Indexación completada![/bold green]")
