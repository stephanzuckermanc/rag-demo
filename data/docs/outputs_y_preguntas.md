# Guia: outputs y como hacer buenas preguntas

Esta guia explica que genera el sistema en `data/output/` y como formular preguntas que den buenas respuestas.

---

## Parte 1 — Que hay en `data/output/`

Cuando corres `python main.py ingest`, GraphRAG construye un grafo de conocimiento y lo guarda en varios archivos. Hay dos tipos: los **legibles** (para humanos) y los **internos** (para el motor).

### Archivos legibles (los que te interesan)

| Archivo | Que es | Para que sirve |
|---------|--------|----------------|
| `report.md` | Reporte completo en Markdown | Resumen de todo lo que aprendio el RAG: insights, entidades, relaciones y el grafo embebido. **Empieza por aqui.** |
| `graph.mmd` | Diagrama Mermaid del grafo | Visualizacion de entidades y como se conectan. Se abre en [mermaid.live](https://mermaid.live), GitHub o Notion. |
| `stats.json` | Estadisticas de la indexacion | Conteos: cuantas entidades, relaciones y comunidades se extrajeron. |

### Archivos internos (datos del motor)

No necesitas abrirlos, pero esto es lo que contienen:

| Archivo | Contenido |
|---------|-----------|
| `entities.parquet` | Las **entidades** detectadas (personas, organizaciones, lugares, eventos) con su descripcion. |
| `relationships.parquet` | Las **relaciones** entre entidades (quien se conecta con quien y como). |
| `communities.parquet` | **Comunidades**: grupos de entidades muy relacionadas entre si. |
| `community_reports.parquet` | Un **reporte narrativo por comunidad** generado por el LLM. Es la base de la busqueda global. |
| `text_units.parquet` | Los **fragmentos (chunks)** originales del texto. Base de la busqueda local y de las citas. |
| `documents.parquet` | Metadatos de los documentos indexados. |
| `lancedb/` | Base de datos vectorial (embeddings) para busqueda por similitud. |
| `context.json` / `*.json` | Estado interno del pipeline. |

> **Idea clave:** GraphRAG no solo parte el texto en pedazos. Identifica QUE entidades hay, COMO se relacionan, y las agrupa en comunidades con un resumen de cada una. Por eso puede responder preguntas tematicas amplias, no solo "buscar el parrafo que coincide".

---

## Parte 2 — Como hacer buenas preguntas

Hay dos modos de busqueda y elegir bien es la mitad del trabajo.

### Global vs Local — cual usar

| | **Global** (default) | **Local** (`--local`) |
|---|---|---|
| **Mira** | Reportes de comunidad (vision de conjunto) | Entidades especificas + sus relaciones + texto original |
| **Buena para** | Temas, tendencias, resumenes, "el panorama general" | Datos puntuales, una entidad concreta, comparaciones especificas |
| **Pregunta tipo** | "Cuales son los temas principales?" | "Que metricas tuvo TikTok?" |
| **Costo** | Mas alta (1 llamada por comunidad + reduce) | Mas baja (1 embedding + 1 completion) |

**Regla rapida:**
- Si tu pregunta empieza con "cuales son", "que tendencias", "resumen de", "que temas" → **global**.
- Si menciona una entidad concreta ("TikTok", "el departamento X", "el contrato Y") → **local** (`--local`).

### Anatomia de una buena pregunta

✅ **Especifica el sujeto.** "Que engagement tuvo Instagram en mayo?" es mejor que "como va todo?".

✅ **Una intencion por pregunta.** Divide "dame metricas de TikTok y tambien las oportunidades de mejora" en dos preguntas.

✅ **Usa el vocabulario de los documentos.** Si el reporte dice "alcance organico", pregunta por "alcance organico", no por "cuanta gente lo vio gratis".

✅ **Pide el formato si lo necesitas.** "Compara TikTok vs Facebook en una lista" orienta la respuesta.

### Ejemplos

| ❌ Pregunta debil | ✅ Pregunta mejorada | Modo |
|---|---|---|
| "Que dice el reporte?" | "Cual es el resumen general y los temas principales del reporte?" | global |
| "Info de redes sociales" | "Que plataforma tuvo mejor engagement y por que?" | local |
| "Numeros" | "Cuales fueron las metricas de TikTok vs Facebook?" | local |
| "Como mejorar" | "Que oportunidades de mejora se identifican en el reporte?" | global |

### Que NO esperar

- **No inventa.** Si la respuesta no esta en los documentos, dice que no la tiene. Eso es lo correcto.
- **No sabe de lo que no indexaste.** Solo conoce los documentos en `data/raw/` al momento del ultimo `ingest`.
- **No hace calculos complejos.** Puede sumar o comparar lo que esta escrito, pero no es una hoja de calculo.

### Si una respuesta no convence

1. **Cambia de modo.** Si usaste global y quedo vago, prueba `--local` (o al reves).
2. **Se mas especifico.** Nombra la entidad o el periodo exacto.
3. **Revisa `report.md`.** Te dice que entidades y temas existen; pregunta sobre lo que SI hay.
4. **Reformula con el vocabulario del documento.**

---

## Flujo recomendado para tu equipo

1. Corre `python main.py ingest` con los documentos en `data/raw/`.
2. Abre `data/output/report.md` para ver de un vistazo que aprendio el sistema.
3. Mira `data/output/graph.mmd` en [mermaid.live](https://mermaid.live) para entender las conexiones.
4. Empieza con una pregunta **global** amplia para ubicarte.
5. Profundiza con preguntas **locales** sobre las entidades que te interesan.
