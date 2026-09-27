# Manufacturing Operations Monitor

A complete local-first industrial operations demo: a Python JSON API, a background telemetry simulator, a persistent SQLite store, OEE and quality summaries, station state, alert acknowledgement, and a responsive browser dashboard. Everything is generated from fictional plant data.

## Run the full local system

From the portfolio repository root, start the API and simulator:

    python3 projects/operations-monitor/server.py

Open http://127.0.0.1:8100/projects/operations-monitor/. The first start creates the local SQLite database and seeds eight hours of sample telemetry. After startup, the simulator records another station reading every five seconds. The dashboard switches to the API automatically, refreshes its KPIs and station/event lists, and persists alert acknowledgements. The database is stored at projects/operations-monitor/data/operations.sqlite3 and excluded from Git.

To use only the static browser preview, serve the repository root with python3 -m http.server 8000 and open http://127.0.0.1:8000/projects/operations-monitor/. GitHub Pages runs the same browser preview. It generates clearly labeled sample values in the browser because Pages does not run the Python service.

## API

All responses are JSON. The local server binds to 127.0.0.1:8100 and exposes:

- GET /api/v1/health — service state and simulation marker.
- GET /api/v1/summary?window=30m|2h|8h — production, availability, performance, quality, OEE, and unacknowledged warnings.
- GET /api/v1/metrics?window=30m|2h|8h — 15-minute production and quality chart buckets.
- GET /api/v1/stations — station state and stored good-unit counts.
- GET /api/v1/events?limit=20 — newest events, with a bounded limit of 1–100.
- POST /api/v1/alerts/{event_id}/ack — acknowledge a sample warning.

The service uses only Python’s standard library. SQL statements are parameterized; the SQLite schema enforces key relationships, allowed states, and nonnegative counters. The simulator retains up to 30 days of local telemetry and events.

## PostgreSQL reference model

The sql directory contains a separate normalized PostgreSQL example for stations, work orders, telemetry, state intervals, production counts, and events. Apply schema.sql, sample_data.sql, and queries.sql to explore its reporting examples. It is a reference model; the runnable API uses SQLite so the demo needs no database installation.

## Industrial scope and boundaries

This is a portfolio system design exercise, not a validated MES or production-ready plant deployment. Its OEE figure is an illustrative estimate over generated samples, not a certified time-weighted calculation. The demo has no PLC, SCADA, Ignition gateway, MQTT broker, plant network, user authentication, or production database connection. It demonstrates API/data/UI boundaries and persisted operational workflows with synthetic data. Before adapting its concepts, define plant tag semantics, shift calendars, downtime rules, ideal cycle times, rework behavior, identity/access controls, retention, alarm policy, and data-quality validation.
