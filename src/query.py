"""Query module: global and local search over the knowledge graph."""

import asyncio
from pathlib import Path

import pandas as pd


def _load_parquet(output_dir: Path, name: str) -> pd.DataFrame:
    """Load a parquet file from output_dir. Raises FileNotFoundError with clear message."""
    path = output_dir / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Falta {name}.parquet. Ejecuta 'python main.py ingest' primero."
        )
    return pd.read_parquet(path)


def _load_optional_parquet(output_dir: Path, name: str) -> pd.DataFrame | None:
    """Load a parquet file, returning None if it doesn't exist."""
    path = output_dir / f"{name}.parquet"
    if not path.exists():
        return None
    return pd.read_parquet(path)


async def _global_search(
    config, output_dir: Path, query: str, community_level: int = 2
) -> tuple[str, dict]:
    """Execute a global search (thematic, map-reduce over communities)."""
    import graphrag.api as api

    entities = _load_parquet(output_dir, "entities")
    communities = _load_parquet(output_dir, "communities")
    community_reports = _load_parquet(output_dir, "community_reports")

    response, context = await api.global_search(
        config=config,
        entities=entities,
        communities=communities,
        community_reports=community_reports,
        community_level=community_level,
        dynamic_community_selection=False,
        response_type="Multiple Paragraphs",
        query=query,
    )
    return response, context


async def _local_search(
    config, output_dir: Path, query: str, community_level: int = 2
) -> tuple[str, dict]:
    """Execute a local search (entity-focused, uses relationships + text units)."""
    import graphrag.api as api

    entities = _load_parquet(output_dir, "entities")
    communities = _load_parquet(output_dir, "communities")
    community_reports = _load_parquet(output_dir, "community_reports")
    text_units = _load_parquet(output_dir, "text_units")
    relationships = _load_parquet(output_dir, "relationships")
    covariates = _load_optional_parquet(output_dir, "covariates")

    response, context = await api.local_search(
        config=config,
        entities=entities,
        communities=communities,
        community_reports=community_reports,
        text_units=text_units,
        relationships=relationships,
        covariates=covariates,
        community_level=community_level,
        response_type="Multiple Paragraphs",
        query=query,
    )
    return response, context


def ask(
    config,
    output_dir: Path,
    query: str,
    local: bool = False,
    community_level: int = 2,
) -> tuple[str, dict]:
    """Sync entry point for search. Bridges async GraphRAG API with Typer."""
    if local:
        return asyncio.run(
            _local_search(config, output_dir, query, community_level)
        )
    return asyncio.run(
        _global_search(config, output_dir, query, community_level)
    )
