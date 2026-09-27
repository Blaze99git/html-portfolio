-- Fictional demonstration rows; timestamps are relative to the current time.
INSERT INTO stations (station_id, station_name, line_name, sequence_number) VALUES
('ST-01', 'Body assembly', 'North Cell', 1),
('ST-02', 'Weld cell', 'North Cell', 2),
('ST-03', 'Surface check', 'North Cell', 3),
('ST-04', 'Powertrain fit', 'North Cell', 4),
('ST-05', 'Final test', 'North Cell', 5),
('ST-06', 'Pack-out', 'North Cell', 6);

INSERT INTO work_orders (work_order_id, product_code, planned_quantity, shift_name, started_at)
VALUES ('DEMO-WO-1042', 'DEMO-A', 1600, 'A', now() - interval '2 hours');

INSERT INTO production_counts (station_id, work_order_id, bucket_start, good_count, reject_count)
VALUES
('ST-01', 'DEMO-WO-1042', date_trunc('minute', now()) - interval '15 minutes', 48, 1),
('ST-02', 'DEMO-WO-1042', date_trunc('minute', now()) - interval '15 minutes', 47, 0),
('ST-03', 'DEMO-WO-1042', date_trunc('minute', now()) - interval '15 minutes', 46, 1),
('ST-04', 'DEMO-WO-1042', date_trunc('minute', now()) - interval '15 minutes', 48, 0),
('ST-05', 'DEMO-WO-1042', date_trunc('minute', now()) - interval '15 minutes', 47, 1),
('ST-06', 'DEMO-WO-1042', date_trunc('minute', now()) - interval '15 minutes', 47, 0);

INSERT INTO station_state_intervals (station_id, state, reason_code, started_at, ended_at)
SELECT station_id, 'running', NULL, now() - interval '2 hours', now() - interval '25 minutes'
FROM stations WHERE line_name = 'North Cell'
UNION ALL
SELECT station_id, 'planned_stop', 'shift_break', now() - interval '25 minutes', now() - interval '15 minutes'
FROM stations WHERE line_name = 'North Cell'
UNION ALL
SELECT station_id, 'running', NULL, now() - interval '15 minutes', now()
FROM stations WHERE line_name = 'North Cell';

INSERT INTO station_events (station_id, work_order_id, event_type, event_state, occurred_at, detail) VALUES
('ST-03', 'DEMO-WO-1042', 'inspection_retry_threshold', 'review', now() - interval '4 minutes', '{"attempt": 2, "source": "portfolio_sample"}'),
('ST-02', 'DEMO-WO-1042', 'weld_cycle_complete', 'normal', now() - interval '7 minutes', '{"cycle_seconds": 71.4, "source": "portfolio_sample"}'),
('ST-06', 'DEMO-WO-1042', 'trace_scan_buffer_watch', 'watch', now() - interval '12 minutes', '{"buffer_units": 8, "source": "portfolio_sample"}');

INSERT INTO telemetry_samples (station_id, tag_name, numeric_value, quality_code, sampled_at) VALUES
('ST-02', 'DEMO.weld_cell.temperature', 24.6, 192, now() - interval '20 seconds'),
('ST-04', 'DEMO.powertrain.pressure', 6.2, 192, now() - interval '25 seconds');
