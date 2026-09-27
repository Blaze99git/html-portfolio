"""Local operations API and synthetic telemetry simulator (Python stdlib only)."""

from __future__ import annotations

import json
import random
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path(__file__).resolve().parent
DB_PATH = PROJECT / "data" / "operations.sqlite3"
LOCK = threading.Lock()
STATIONS = [
    ("ST-01", "Body assembly", "Workpiece load", "RUNNING", 18.0),
    ("ST-02", "Weld cell", "Weld cycle", "RUNNING", 22.0),
    ("ST-03", "Surface check", "Quality inspection", "ATTENTION", 24.0),
    ("ST-04", "Powertrain fit", "Torque verification", "RUNNING", 20.0),
    ("ST-05", "Final test", "End-of-line check", "RUNNING", 26.0),
    ("ST-06", "Pack-out", "Trace scan", "IDLE", 16.0),
]


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def initialize() -> None:
    with connect() as db:
        db.execute("PRAGMA journal_mode = WAL")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS stations (
              station_id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              operation TEXT NOT NULL,
              state TEXT NOT NULL CHECK(state IN ('RUNNING','ATTENTION','IDLE','OFFLINE')),
              ideal_cycle_seconds REAL NOT NULL CHECK(ideal_cycle_seconds > 0)
            );
            CREATE TABLE IF NOT EXISTS telemetry (
              id INTEGER PRIMARY KEY,
              station_id TEXT NOT NULL REFERENCES stations(station_id),
              observed_at TEXT NOT NULL,
              cycle_seconds REAL NOT NULL CHECK(cycle_seconds >= 0),
              good_units INTEGER NOT NULL CHECK(good_units >= 0),
              rejected_units INTEGER NOT NULL CHECK(rejected_units >= 0),
              state TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(observed_at);
            CREATE INDEX IF NOT EXISTS idx_telemetry_station_time ON telemetry(station_id, observed_at);
            CREATE TABLE IF NOT EXISTS events (
              event_id TEXT PRIMARY KEY,
              station_id TEXT NOT NULL REFERENCES stations(station_id),
              opened_at TEXT NOT NULL,
              message TEXT NOT NULL,
              severity TEXT NOT NULL CHECK(severity IN ('INFO','WARNING','ALARM')),
              acknowledged INTEGER NOT NULL DEFAULT 0 CHECK(acknowledged IN (0,1))
            );
            CREATE INDEX IF NOT EXISTS idx_events_time ON events(opened_at);
        """)
        if not db.execute("SELECT 1 FROM stations LIMIT 1").fetchone():
            db.executemany(
                "INSERT INTO stations VALUES (?,?,?,?,?)",
                STATIONS,
            )
        if not db.execute("SELECT 1 FROM telemetry LIMIT 1").fetchone():
            rng = random.Random(2030)
            now = datetime.now(timezone.utc)
            for offset in range(96, 0, -1):
                recorded_at = (now - timedelta(minutes=offset * 5)).isoformat()
                for station_id, _, _, state, ideal in STATIONS:
                    if state == "IDLE" and rng.random() < 0.8:
                        continue
                    reject = int(rng.random() < 0.025)
                    db.execute(
                        "INSERT INTO telemetry(station_id,observed_at,cycle_seconds,good_units,rejected_units,state) VALUES(?,?,?,?,?,?)",
                        (station_id, recorded_at, max(ideal * 0.8, rng.gauss(ideal * 1.08, 1.7)), 1 - reject, reject, state),
                    )
        if not db.execute("SELECT 1 FROM events LIMIT 1").fetchone():
            now = datetime.now(timezone.utc)
            for index, (station_id, _, _, _, _) in enumerate(STATIONS[:5]):
                message, severity = (
                    ("Inspection retry threshold", "WARNING") if index == 0 else
                    ("Material buffer low", "WARNING") if index == 1 else
                    ("Weld cycle complete", "INFO") if index == 2 else
                    ("Torque verification recorded", "INFO") if index == 3 else
                    ("Line heartbeat restored", "INFO")
                )
                db.execute(
                    "INSERT INTO events VALUES (?,?,?,?,?,?)",
                    (f"EV-{1042-index}", station_id, (now - timedelta(minutes=index + 1)).isoformat(), message, severity, 0),
                )


def record_sample(rng: random.Random, tick: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with LOCK, connect() as db:
        station = STATIONS[tick % len(STATIONS)]
        station_id, name, operation, base_state, ideal = station
        state = "ATTENTION" if station_id == "ST-03" and tick % 8 == 0 else base_state
        available = state in {"RUNNING", "ATTENTION"}
        reject = int(available and rng.random() < (0.09 if state == "ATTENTION" else 0.025))
        cycle = max(ideal * 0.75, rng.gauss(ideal * 1.08, 1.8)) if available else 0.0
        db.execute(
            "INSERT INTO telemetry(station_id,observed_at,cycle_seconds,good_units,rejected_units,state) VALUES(?,?,?,?,?,?)",
            (station_id, now, cycle, int(available) - reject, reject, state),
        )
        db.execute("UPDATE stations SET state=? WHERE station_id=?", (state, station_id))
        if tick % 9 == 0:
            db.execute("UPDATE stations SET state='RUNNING' WHERE station_id=? AND state='ATTENTION'", (station_id,))
        if tick % 19 == 0:
            event_id = f"EV-{int(time.time())}-{tick}"
            db.execute(
                "INSERT INTO events VALUES (?,?,?,?,?,0)",
                (event_id, station_id, now, f"{operation} cycle recorded", "INFO"),
            )
        # Keep the local demo database bounded while preserving 30 days of telemetry.
        db.execute("DELETE FROM telemetry WHERE observed_at < ?", ((datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),))
        db.execute("DELETE FROM events WHERE opened_at < ?", ((datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),))


def simulate() -> None:
    rng = random.Random()
    tick = 0
    while True:
        tick += 1
        try:
            record_sample(rng, tick)
        except sqlite3.Error as error:
            print(f"Simulator database error: {error}")
        time.sleep(5)


def summary(window: str) -> dict:
    durations = {"30m": 30, "2h": 120, "8h": 480}
    if window not in durations:
        window = "30m"
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=durations[window])).isoformat()
    with connect() as db:
        rows = db.execute("SELECT t.cycle_seconds,t.good_units,t.rejected_units,t.state,s.ideal_cycle_seconds FROM telemetry AS t JOIN stations AS s USING(station_id) WHERE t.observed_at >= ?", (cutoff,)).fetchall()
        station_count = db.execute("SELECT COUNT(*) FROM stations").fetchone()[0]
        running_count = db.execute("SELECT COUNT(*) FROM stations WHERE state IN ('RUNNING','ATTENTION')").fetchone()[0]
        open_alerts = db.execute("SELECT COUNT(*) FROM events WHERE severity='WARNING' AND acknowledged=0").fetchone()[0]
    good = sum(row["good_units"] for row in rows)
    rejected = sum(row["rejected_units"] for row in rows)
    availability = (running_count / station_count * 100) if station_count else 0.0
    cycle_total = sum(row["cycle_seconds"] for row in rows if row["cycle_seconds"] > 0)
    ideal_total = sum(row["ideal_cycle_seconds"] for row in rows if row["cycle_seconds"] > 0)
    performance = min(100.0, ideal_total / cycle_total * 100) if cycle_total else 0.0
    quality = good / (good + rejected) * 100 if good + rejected else 0.0
    return {
        "window": window,
        "units_completed": good,
        "availability": round(availability, 1),
        "performance": round(performance, 1),
        "quality": round(quality, 1),
        "oee": round(availability * performance * quality / 10_000, 1),
        "open_alerts": open_alerts,
        "sample_count": len(rows),
        "sampled_at": datetime.now(timezone.utc).isoformat(),
    }


def metrics(window: str) -> dict:
    durations = {"30m": 30, "2h": 120, "8h": 480}
    if window not in durations:
        window = "30m"
    duration_minutes = durations[window]
    bucket_count = duration_minutes // 15
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=duration_minutes)
    cutoff_iso = cutoff.isoformat()
    with connect() as db:
        rows = db.execute(
            "SELECT observed_at,good_units,rejected_units FROM telemetry WHERE observed_at >= ? ORDER BY observed_at",
            (cutoff_iso,),
        ).fetchall()
    good = [0] * bucket_count
    rejected = [0] * bucket_count
    start = cutoff.timestamp()
    for row in rows:
        observed = datetime.fromisoformat(row["observed_at"]).timestamp()
        bucket = min(bucket_count - 1, max(0, int((observed - start) // 900)))
        good[bucket] += row["good_units"]
        rejected[bucket] += row["rejected_units"]
    production = [good[index] + rejected[index] for index in range(bucket_count)]
    quality = [
        round(good[index] / production[index] * 100, 1) if production[index] else 0.0
        for index in range(bucket_count)
    ]
    return {
        "window": window,
        "interval_minutes": 15,
        "production_units": production,
        "quality_percent": quality,
    }


class OperationsHandler(SimpleHTTPRequestHandler):
    server_version = "NorthCellDemo/1.0"
    sys_version = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        request = urlparse(self.path)
        if not request.path.startswith("/api/v1/"):
            self.path = request.path
            return super().do_GET()
        query = parse_qs(request.query)
        with LOCK, connect() as db:
            if request.path == "/api/v1/health":
                self.json(200, {"status": "ok", "service": "north-cell-operations-api", "generated_data": True})
            elif request.path == "/api/v1/summary":
                self.json(200, summary(query.get("window", ["30m"])[0]))
            elif request.path == "/api/v1/metrics":
                self.json(200, metrics(query.get("window", ["30m"])[0]))
            elif request.path == "/api/v1/stations":
                rows = db.execute("SELECT station_id,name,operation,state FROM stations ORDER BY station_id").fetchall()
                counts = {row["station_id"]: row["count"] for row in db.execute("SELECT station_id,SUM(good_units) AS count FROM telemetry GROUP BY station_id")}
                self.json(200, {"items": [dict(row) | {"units_completed": counts.get(row["station_id"], 0)} for row in rows]})
            elif request.path == "/api/v1/events":
                try:
                    limit = max(1, min(100, int(query.get("limit", ["20"])[0])))
                except ValueError:
                    self.json(400, {"error": "limit must be an integer between 1 and 100"})
                    return
                rows = db.execute("SELECT event_id,station_id,opened_at,message,severity,acknowledged FROM events ORDER BY opened_at DESC LIMIT ?", (limit,)).fetchall()
                self.json(200, {"items": [dict(row) for row in rows]})
            else:
                self.json(404, {"error": "API route not found"})

    def do_POST(self):
        request = urlparse(self.path)
        prefix = "/api/v1/alerts/"
        if not request.path.startswith(prefix) or not request.path.endswith("/ack"):
            self.json(404, {"error": "API route not found"})
            return
        event_id = request.path[len(prefix):-4].strip("/")
        if not event_id or len(event_id) > 80:
            self.json(400, {"error": "invalid event id"})
            return
        with LOCK, connect() as db:
            cursor = db.execute("UPDATE events SET acknowledged=1 WHERE event_id=? AND severity='WARNING'", (event_id,))
            if not cursor.rowcount:
                self.json(404, {"error": "unacknowledged alert not found"})
                return
        self.json(200, {"event_id": event_id, "acknowledged": True})

    def json(self, status: int, data: dict):
        payload = json.dumps(data, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        super().log_message(fmt, *args)


if __name__ == "__main__":
    initialize()
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("127.0.0.1", 8100), OperationsHandler)
    threading.Thread(target=simulate, daemon=True).start()
    print("Operations demo: http://127.0.0.1:8100/projects/operations-monitor/")
    print("API health: http://127.0.0.1:8100/api/v1/health")
    print("Bound to localhost only; synthetic telemetry is persisted in projects/operations-monitor/data/operations.sqlite3.")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping operations demo.")
        server.server_close()
