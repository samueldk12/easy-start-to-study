-- ClickHouse Real-time Analytics Setup for veloceg-teste
CREATE DATABASE IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.events (
    event_id UUID DEFAULT generateUUIDv4(),
    user_id UInt64,
    event_type LowCardinality(String),
    event_timestamp DateTime DEFAULT now(),
    payload String
) ENGINE = MergeTree()
ORDER BY (event_type, event_timestamp);
