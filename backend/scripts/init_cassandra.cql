CREATE KEYSPACE IF NOT EXISTS store
WITH replication = {
    'class': 'NetworkTopologyStrategy',
    'datacenter1': 3
} AND durable_writes = true;

CREATE KEYSPACE IF NOT EXISTS store_test
WITH replication = {
    'class': 'NetworkTopologyStrategy',
    'datacenter1': 3
} AND durable_writes = true;
