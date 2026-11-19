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
ACTION = OperationType.UPDATE_PRODUCT
START = datetime(2000, 1, 1, 12, tzinfo=UTC)
END = datetime(2000, 1, 1, 12, 1, tzinfo=UTC)

session = get_cassandra_session()
try:
    config = settings.cassandra
    history = CassandraHistoryRepository(
        session, config.bucket_seconds_type, config.bucket_seconds_entity,
        config.bucket_seconds_user,
    )

    def read():
        return history.get_events_by_type(ACTION, START, END, limit=20)

    seed = read()
    if len(seed) != 20:
        sys.exit("Expected 20 prepared events in Cassandra.")
    example = seed[0]

    def write():
        history.add_event(OperationEvent(
            user_id=example.user_id, target_id=example.target_id, action=ACTION,
        ))

    output = csv.writer(sys.stdout, lineterminator="\n")
    output.writerow([
        "operation", "clients", "attempts", "success", "error_pct",
        "throughput_ops_s", "mean_ms", "p95_ms",
    ])
    for operation in (read, write):
        def measure(_):
            started = perf_counter()
            try:
                operation()
            except (DriverException, NoHostAvailable):
                return None
            return (perf_counter() - started) * 1000

        for clients in (1, 4, 16, 32):
            with ThreadPoolExecutor(max_workers=clients) as workers:
                list(workers.map(measure, range(2 * clients)))
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
