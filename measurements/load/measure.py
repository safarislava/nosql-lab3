"""Measure the history repository at several concurrency levels."""

import csv
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from math import ceil
from statistics import mean
from time import perf_counter

from cassandra import DriverException
from cassandra.cluster import NoHostAvailable

from domain.history import OperationEvent, OperationType
from infrastructure.environment.settings import settings
from infrastructure.persistence.cassandra.connection import get_cassandra_session
from infrastructure.persistence.cassandra.history_repository import (
    CassandraHistoryRepository,
)

ATTEMPTS = 2000
WARMUP_ATTEMPTS = 10
ACTION = OperationType.UPDATE_PRODUCT
START = datetime(2000, 1, 1, 12, tzinfo=UTC)
END = datetime(2000, 1, 1, 12, 1, tzinfo=UTC)

order = sys.argv[1:]
if order not in ([], ["read-first"], ["write-first"]):
    sys.exit("Usage: measure.py [read-first|write-first]")

session = get_cassandra_session()
try:
    config = settings.cassandra
    history = CassandraHistoryRepository(
        session, config.bucket_seconds_type, config.bucket_seconds_entity,
        config.bucket_seconds_user,
    )

    seed = history.get_events_by_type(ACTION, START, END, limit=1)
    if not seed:
        sys.exit("Expected a prepared event in Cassandra.")
    example = seed[0]
    select_event = session.prepare("""
        SELECT event_type, bucket, event_id, entity_type, entity_id, user_id, timestamp, details
        FROM events_by_type
        WHERE event_type = ? AND bucket = ? AND event_id = ?
    """)
    read_key = (ACTION.value, int(example.timestamp.timestamp() // config.bucket_seconds_type), example.id)

    def read():
        row = session.execute(select_event, read_key).one()
        if row is None:
            raise RuntimeError("Expected the prepared event at its primary key.")
        return history._row_to_event(row)

    insert_event = session.prepare("""
        INSERT INTO events_by_type (
            event_type, bucket, event_id, entity_type, entity_id, user_id, timestamp, details
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """)

    def write():
        event = OperationEvent(
            user_id=example.user_id, target_id=example.target_id, action=ACTION,
        )
        bucket = int(event.timestamp.timestamp() // config.bucket_seconds_type)
        session.execute(insert_event, (
            ACTION.value, bucket, event.id, "PRODUCT",
            event.target_id or event.user_id, event.user_id, event.timestamp, "{}",
        ))

    output = csv.writer(sys.stdout, lineterminator="\n")
    output.writerow([
        "operation", "clients", "attempts", "success", "error_pct",
        "throughput_ops_s", "mean_ms", "p95_ms",
    ])
    operations = (read, write) if order == ["read-first"] else (write, read)
    for operation in operations:
        def measure(_):
            started = perf_counter()
            try:
                operation()
            except (DriverException, NoHostAvailable):
                return None
            return (perf_counter() - started) * 1000

        for clients in (1, 4, 8, 16, 32, 64, 128, 256):
            with ThreadPoolExecutor(max_workers=clients) as workers:
                list(workers.map(measure, range(WARMUP_ATTEMPTS)))
                started = perf_counter()
                times = list(workers.map(measure, range(ATTEMPTS)))
                elapsed = perf_counter() - started

            successful = sorted(ms for ms in times if ms is not None)
            count = len(successful)
            output.writerow([
                operation.__name__, clients, ATTEMPTS, count,
                round(100 * (ATTEMPTS - count) / ATTEMPTS, 2),
                round(count / elapsed, 2),
                round(mean(successful), 3) if count else "",
                round(successful[ceil(0.95 * count) - 1], 3) if count else "",
            ])
finally:
    session.cluster.shutdown()
