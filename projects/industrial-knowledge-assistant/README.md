# Industrial Knowledge Assistant

A deterministic, citation-first retrieval demo over eight fictional industrial notes. It illustrates document ingestion, lightweight intent routing, relevance ranking, source references, and an optional local Python API. It has no generative model or connection to employer/client systems.

## Run the browser and local API demo

From the portfolio repository root:

```bash
python3 projects/industrial-knowledge-assistant/run_demo.py
```

Open `http://127.0.0.1:8000/projects/industrial-knowledge-assistant/`. The local server exposes `GET /projects/industrial-knowledge-assistant/api/health` and `GET /projects/industrial-knowledge-assistant/api/ask?q=...`. It binds to `127.0.0.1`, limits questions to 240 characters, and does not include question text in its access log. On GitHub Pages, the browser uses the same bundled JSON corpus with a JavaScript implementation instead. No package installation, key, model service, or outbound request is needed.

## Ingest and query the knowledge base

The Markdown source files under `data/source_docs/` are the editable source of truth. Each has a small metadata header, category, section, revision, and fictional body. Regenerate the normalized JSON index from the portfolio root:

```bash
python3 projects/industrial-knowledge-assistant/ingest.py
```

The ingestion step validates required metadata and unique IDs, limits document size, computes a SHA-256 digest for each source, and writes stable JSON. The Python API can also be queried directly from this folder:

```bash
cd projects/industrial-knowledge-assistant
python3 -c 'from engine import answer; print(answer("What should I do after an air pressure alarm?"))'
```

## Retrieval flow

The engine routes queries into maintenance, quality, signal-data, or operations categories using transparent keyword rules, then ranks candidate documents with a small TF-IDF-style lexical score. If the routed category has no match, it falls back to the full sample library. Results include the route, source ID, title, section, revision, matching terms, and excerpt. The response is composed from the first returned passage; it does not generate unsupported steps. Python unit tests cover routing, citations, empty results, input limits, deterministic ranking, and ingestion validation.

## Boundaries

This small corpus is deliberately fictional. Search quality is lexical and the intent rules are hand-authored; it is not semantic search, an LLM, a production RAG service, or validated operational guidance. It has no authentication, authorization, audit store, document permissions, or production integration. Do not apply its example procedures to real equipment.
