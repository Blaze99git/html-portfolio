-- Portfolio demo schema. All names and records are fictional.
CREATE TABLE stations (
    station_id       text PRIMARY KEY,
    station_name     text NOT NULL,
    line_name        text NOT NULL,
    sequence_number  smallint NOT NULL CHECK (sequence_number > 0),
    ideal_cycle_seconds numeric(8, 3) NOT NULL DEFAULT 75 CHECK (ideal_cycle_seconds > 0),
    enabled          boolean NOT NULL DEFAULT true
);

CREATE TABLE work_orders (
    work_order_id    text PRIMARY KEY,
    product_code     text NOT NULL,
    planned_quantity integer NOT NULL CHECK (planned_quantity >= 0),
    shift_name       text NOT NULL,
    started_at       timestamptz NOT NULL
);

CREATE TABLE station_events (
    event_id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    station_id       text NOT NULL REFERENCES stations(station_id),
    work_order_id    text REFERENCES work_orders(work_order_id),
    event_type       text NOT NULL,
    event_state      text NOT NULL CHECK (event_state IN ('normal', 'watch', 'review')),
    occurred_at      timestamptz NOT NULL,
    detail           jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX station_events_time_idx ON station_events (occurred_at DESC);
CREATE INDEX station_events_station_time_idx ON station_events (station_id, occurred_at DESC);

CREATE TABLE station_state_intervals (
    interval_id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    station_id       text NOT NULL REFERENCES stations(station_id),
    state            text NOT NULL CHECK (state IN ('running', 'planned_stop', 'unplanned_stop', 'idle')),
    reason_code      text,
    started_at       timestamptz NOT NULL,
    ended_at         timestamptz,
    CHECK (ended_at IS NULL OR ended_at > started_at)
);
CREATE INDEX station_state_time_idx ON station_state_intervals (station_id, started_at DESC);

CREATE TABLE telemetry_samples (
    sample_id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    station_id       text NOT NULL REFERENCES stations(station_id),
    tag_name         text NOT NULL,
    numeric_value    double precision NOT NULL,
    quality_code     smallint NOT NULL DEFAULT 192,
    sampled_at       timestamptz NOT NULL
);
CREATE INDEX telemetry_tag_time_idx ON telemetry_samples (tag_name, sampled_at DESC);

CREATE TABLE production_counts (
    station_id       text NOT NULL REFERENCES stations(station_id),
    work_order_id    text NOT NULL REFERENCES work_orders(work_order_id),
    bucket_start     timestamptz NOT NULL,
    good_count       integer NOT NULL DEFAULT 0 CHECK (good_count >= 0),
    reject_count     integer NOT NULL DEFAULT 0 CHECK (reject_count >= 0),
    PRIMARY KEY (station_id, work_order_id, bucket_start)
);
