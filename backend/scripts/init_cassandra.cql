CREATE KEYSPACE IF NOT EXISTS store
WITH replication = {
    'class': 'NetworkTopologyStrategy',
    'datacenter1': 3
} AND durable_writes = true;

CREATE TABLE IF NOT EXISTS store.events_by_type (
    event_type text,
    bucket bigint,
    event_id timeuuid,
    entity_type text,
    entity_id uuid,
    user_id uuid,
    timestamp timestamp,
    details text,
    PRIMARY KEY ((event_type, bucket), event_id)
) WITH CLUSTERING ORDER BY (event_id DESC);

CREATE TABLE IF NOT EXISTS store.events_by_entity (
    entity_type text,
    entity_id uuid,
    bucket bigint,
    event_id timeuuid,
    event_type text,
    user_id uuid,
    timestamp timestamp,
    details text,
    PRIMARY KEY ((entity_type, entity_id, bucket), event_id)
) WITH CLUSTERING ORDER BY (event_id DESC);

CREATE TABLE IF NOT EXISTS store.events_by_user (
    user_id uuid,
    bucket bigint,
    event_id timeuuid,
    event_type text,
    entity_type text,
    entity_id uuid,
    timestamp timestamp,
    details text,
    PRIMARY KEY ((user_id, bucket), event_id)
) WITH CLUSTERING ORDER BY (event_id DESC);
