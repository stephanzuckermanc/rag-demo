# graphrag-demo

Demo de Knowledge Graph RAG usando [Microsoft GraphRAG](https://github.com/microsoft/graphrag) con Gemini como backend de IA.

GraphRAG construye un grafo de conocimiento a partir de tus documentos y permite hacer preguntas con contexto enriquecido.

## Requisitos

- Python 3.10+
- Una API key de Gemini (gratuita)

## Instalacion

```bash
git clone <repo-url>
cd graphrag-demo
python3 -m venv venv
source venv/bin/activate
pip install -r config/requirements.txt
```

## Configuracion

1. Obtener una API key gratuita en [Google AI Studio](https://aistudio.google.com)
2. Al ejecutar cualquier comando por primera vez, el CLI te pedira la key y la guardara automaticamente en `config/.env`

O manualmente:

```bash
cp config/.env.example config/.env
```

Variables de entorno en `config/.env`:

```
GEMINI_API_KEY=tu-api-key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

## Estructura del proyecto

```
graphrag-demo/
├── main.py                   # CLI principal (ingest, ask, status, graph, report)
├── config/
│   ├── settings.yaml         # configuracion de GraphRAG
│   ├── requirements.txt      # dependencias Python
│   ├── .env                  # API key y modelos (gitignored)
│   └── .env.example          # template de .env
├── scripts/
│   └── demo.py               # script de demo automatizado
├── src/
│   ├── ingest.py             # conversion de docs + indexacion
│   ├── query.py              # busqueda global y local
│   └── utils.py              # utilidades compartidas
└── data/
    ├── raw/                  # documentos originales (PDF, DOCX, MD, TXT)
    ├── docs/                 # documentacion del proyecto
    │   └── commands.md       # referencia de comandos del CLI
    ├── prompts/              # templates de prompts (configurados en espanol)
    ├── input/                # texto plano convertido (auto-generado)
    ├── output/               # grafo, reportes, diagramas (auto-generado)
    ├── cache/                # cache de llamadas al LLM (auto-generado)
    └── logs/                 # logs de indexacion (auto-generado)
```

## Comandos

### `ingest` — Indexar documentos

Coloca tus archivos en `data/raw/` (PDF, DOCX, MD, TXT) y ejecuta:

```bash
python main.py ingest
```

Convierte los documentos a texto plano y construye el grafo de conocimiento. La primera vez puede tomar varios minutos.

### `ask` — Hacer preguntas

Busqueda **global** (temas generales, resumenes):

```bash
python main.py ask "Cuales son los temas principales en estos documentos?"
```

Busqueda **local** (entidades especificas):

```bash
python main.py ask "Que relacion tiene X con Y?" --local
```

### `status` — Ver estado

```bash
python main.py status
```

Muestra documentos indexados, entidades, relaciones, comunidades y fecha de ultima indexacion.

### `graph` — Generar diagrama Mermaid

```bash
python main.py graph
```

Genera `data/output/graph.mmd`. Se puede visualizar en GitHub, Notion o [mermaid.live](https://mermaid.live).

### `report` — Generar reporte completo

```bash
python main.py report
```

Genera `data/output/report.md` con insights del grafo, catalogo de entidades, tabla de relaciones y diagrama Mermaid embebido.

### Demo automatizado

```bash
python scripts/demo.py
```

Ejecuta una serie de preguntas predefinidas y muestra las respuestas formateadas.

## Tipos de busqueda

| Tipo | Cuando usarla | Ejemplo |
|---|---|---|
| **Global** (default) | Preguntas tematicas, resumenes, tendencias | "Cuales son los riesgos principales?" |
| **Local** (`--local`) | Preguntas sobre entidades especificas | "Que hace el departamento X?" |

## Consumo de tokens y llamadas a la API

GraphRAG hace llamadas a Gemini en dos momentos: durante la **indexacion** y durante las **consultas**.

### Indexacion (`ingest`)

La indexacion es el paso mas costoso. GraphRAG hace multiples llamadas al LLM:

| Paso | Modelo | Que hace | Llamadas aprox. |
|------|--------|----------|-----------------|
| Extraccion de entidades | Completion | Identifica entidades y relaciones en cada chunk | 1-2 por chunk |
| Resumen de descripciones | Completion | Consolida descripciones duplicadas de una entidad | 1 por entidad duplicada |
| Reportes de comunidad | Completion | Genera un reporte narrativo por comunidad | 1 por comunidad |
| Embeddings | Embedding | Genera vectores para entidades, comunidades y text units | 1 por batch |

**Ejemplo real**: un PDF de ~8K caracteres (4 chunks) genero ~50 llamadas y tomo ~2 minutos.

**Estimacion**: para C chunks totales, espera `C * 2 + entidades + comunidades` llamadas de completion + unas pocas de embedding.

### Consultas (`ask`)

Las consultas son mucho mas baratas:

| Tipo | Modelo | Llamadas por consulta |
|------|--------|----------------------|
| **Global** | Completion | 1 map por comunidad + 1 reduce |
| **Local** | Completion + Embedding | 1 embedding + 1 completion |

### Comandos que NO consumen tokens

| Comando | Descripcion |
|---------|-------------|
| `status` | Solo lee archivos locales |
| `graph` | Solo lee parquets y genera Mermaid |
| `report` | Solo lee parquets y genera Markdown |

### Tips para minimizar costos

- Usa `gemini-2.5-flash` (default) — el mas rapido y barato
- Empieza con pocos documentos para probar
- La re-indexacion es costosa — solo re-indexa cuando agregues documentos nuevos
- El cache en `data/cache/` evita llamadas repetidas al re-indexar el mismo contenido
- Busqueda local es mas barata que global para consultas simples
- La API key de AI Studio tiene una capa gratuita generosa

## Configuracion avanzada

Editar `config/settings.yaml` para ajustar:

- **Modelo LLM**: cambiar `GEMINI_MODEL` en `config/.env`
- **Chunk size**: `chunking.size` (default 1200) — mas grande = mas contexto, menos llamadas
- **Chunk overlap**: `chunking.overlap` (default 100) — solapamiento entre fragmentos
- **Community level**: `--level` en el comando `ask` (default 2)
- **Idioma**: los prompts en `data/prompts/` estan configurados para generar en espanol

## Solucion de problemas

**"No se encontraron documentos"** — Coloca archivos en `data/raw/`, no en `data/input/`.

**"No se encontro un indice"** — Ejecuta `python main.py ingest` primero.

**Rate limit (429)** — Espera unos segundos y reintenta. GraphRAG tiene reintentos automaticos con backoff exponencial.

**PDF sin texto** — Los PDFs escaneados (imagenes) no producen texto. Usa OCR (Tesseract) para pre-procesarlos.
