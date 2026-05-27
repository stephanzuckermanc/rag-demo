# Referencia de comandos

## `ingest` — Indexar documentos

```bash
python main.py ingest
```

Convierte los documentos de `data/raw/` (PDF, DOCX, MD, TXT) a texto plano en `data/input/` y construye el grafo de conocimiento. La primera ejecucion puede tomar varios minutos dependiendo del volumen de documentos.

**Consume tokens:** Si. Multiples llamadas al LLM por chunk de texto.

---

## `ask` — Hacer preguntas

**Global** (temas generales, resumenes):

```bash
python main.py ask "Cuales son los temas principales?"
```

**Local** (entidades especificas):

```bash
python main.py ask "Que relacion tiene X con Y?" --local
```

**Opciones:**

| Flag | Default | Descripcion |
|------|---------|-------------|
| `--local` | `False` | Usa busqueda local en vez de global |
| `--level` | `2` | Nivel de comunidad para busqueda global |

**Consume tokens:** Si. Global: 1 map por comunidad + 1 reduce. Local: 1 embedding + 1 completion.

---

## `status` — Ver estado del indice

```bash
python main.py status
```

Muestra: documentos indexados, entidades, relaciones, comunidades y fecha de ultima indexacion.

**Consume tokens:** No. Solo lee archivos locales.

---

## `graph` — Generar diagrama Mermaid

```bash
python main.py graph
```

Genera `data/output/graph.mmd` con un diagrama del grafo de conocimiento, nodos coloreados por tipo de entidad.

**Consume tokens:** No. Solo lee parquets y genera Mermaid.

---

## `report` — Generar reporte completo

```bash
python main.py report
```

Genera `data/output/report.md` con:
- Insights del grafo (reportes de comunidad)
- Catalogo de entidades con descripciones
- Tabla de relaciones
- Diagrama Mermaid embebido

**Consume tokens:** No. Solo lee parquets y genera Markdown.

---

## `demo` — Demo automatizado

```bash
python scripts/demo.py
```

Ejecuta una serie de preguntas predefinidas y muestra las respuestas formateadas con tiempos de ejecucion.

**Consume tokens:** Si. Ejecuta multiples consultas global y local.
