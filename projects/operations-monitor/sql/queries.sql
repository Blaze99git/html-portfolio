-- Eight-hour line view. State intervals are clipped to the reporting window so
-- an event that crosses a window boundary contributes only its overlap.
WITH bounds AS (
    SELECT now() - interval '8 hours' AS window_start, now() AS window_end
), state_seconds AS (
    SELECT si.station_id,
           sum(extract(epoch FROM least(coalesce(si.ended_at, b.window_end), b.window_end)
                        - greatest(si.started_at, b.window_start)))
               FILTER (WHERE si.state <> 'planned_stop') AS planned_seconds,
           sum(extract(epoch FROM least(coalesce(si.ended_at, b.window_end), b.window_end)
                        - greatest(si.started_at, b.window_start)))
               FILTER (WHERE si.state = 'running') AS operating_seconds
    FROM station_state_intervals AS si
    CROSS JOIN bounds AS b
    WHERE si.started_at < b.window_end
      AND coalesce(si.ended_at, b.window_end) > b.window_start
    GROUP BY si.station_id
), production AS (
    SELECT station_id,
           sum(good_count) AS good_units,
           sum(reject_count) AS rejected_units,
           sum(good_count + reject_count) AS total_units
    FROM production_counts
    CROSS JOIN bounds
    WHERE bucket_start >= window_start AND bucket_start < window_end
    GROUP BY station_id
), ratios AS (
    SELECT s.station_id,
           s.station_name,
           coalesce(p.good_units, 0) AS good_units,
           coalesce(p.rejected_units, 0) AS rejected_units,
           least(1.0, coalesce(ss.operating_seconds / nullif(ss.planned_seconds, 0), 0)) AS availability,
           least(1.0, coalesce((p.total_units * s.ideal_cycle_seconds)
                               / nullif(ss.operating_seconds, 0), 0)) AS performance,
           coalesce(p.good_units::numeric / nullif(p.total_units, 0), 0) AS quality
    FROM stations AS s
    LEFT JOIN state_seconds AS ss USING (station_id)
    LEFT JOIN production AS p USING (station_id)
    WHERE s.enabled
)
SELECT station_id,
       station_name,
       good_units,
       rejected_units,
       round(100 * availability, 1) AS availability_pct,
       round(100 * performance, 1) AS performance_pct,
       round(100 * quality, 1) AS quality_pct,
       round(100 * availability * performance * quality, 1) AS oee_pct
FROM ratios
ORDER BY station_id;

-- Hourly first-pass yield by station.
SELECT s.station_name,
       date_trunc('hour', p.bucket_start) AS hour_start,
       sum(p.good_count) AS good_units,
       sum(p.reject_count) AS rejects,
       round(100.0 * sum(p.good_count)
             / NULLIF(sum(p.good_count + p.reject_count), 0), 2) AS first_pass_yield_pct
FROM production_counts AS p
JOIN stations AS s USING (station_id)
WHERE p.bucket_start >= now() - interval '8 hours'
GROUP BY s.station_name, date_trunc('hour', p.bucket_start)
ORDER BY hour_start, s.station_name;

-- Most recent event for every station using PostgreSQL DISTINCT ON.
SELECT DISTINCT ON (station_id)
       station_id, event_type, event_state, occurred_at
FROM station_events
ORDER BY station_id, occurred_at DESC;
