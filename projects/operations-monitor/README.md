# Manufacturing Operations Monitor

An original portfolio simulation of a small manufacturing cell. It combines an interactive browser dashboard with a PostgreSQL example model for stations, work orders, telemetry, production intervals, quality checks, and events. All values and station names are invented for this demo.

## Run the browser demo

From the portfolio repository root:

```bash
python3 -m http.server 8000
```

Open `http://127.0.0.1:8000/projects/operations-monitor/`. The page models production rate, availability/performance/quality components and OEE, first-pass yield, station state, and recent alerts. Try selecting a time range, filtering events by station, acknowledging a sample alert, pausing the simulation, and exporting a CSV summary. State resets when you reload; the dashboard has no database or remote service.

## PostgreSQL example

The `sql/` directory contains a normalized schema, generated sample rows, and example analytical queries. Create a local database, then apply `schema.sql`, `sample_data.sql`, and `queries.sql` in that order. The queries calculate shift-window OEE from clipped station-state intervals, hourly first-pass yield, and a station's latest events.

This is a reference model, not a complete MES or validated plant implementation. Before adapting it, define local event semantics, shift calendars, planned downtime, ideal cycle time, rework rules, access controls, retention, and data-quality checks.

## Boundaries

The browser simulation generates its values in JavaScript. SQL sample rows are fictional. There is no PLC, SCADA, Ignition, plant network, or production-database connection, and the project contains no employer or customer source material.
