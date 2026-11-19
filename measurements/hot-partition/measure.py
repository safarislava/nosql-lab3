"""Write two comparable workloads to store.events_by_type."""

import csv
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from math import ceil
from statistics import mean
from time import perf_counter
from uuid import uuid4

from cassandra import ConsistencyLevel, DriverException
from cassandra.cluster import NoHostAvailable
from cassandra.util import uuid_from_time

from infrastructure.persistence.cassandra.connection import get_cassandra_session

TYPES = (
    "UPDATE_PRODUCT", "CREATE_PRODUCT", "DELETE_PRODUCT", "RESERVE_STOCK",
    "RESTORE_STOCK", "UPLOAD_ATTACHMENT", "UPDATE_ATTACHMENT",
    "DELETE_ATTACHMENT", "ASSIGN_PRODUCT_CATEGORY", "REMOVE_PRODUCT_CATEGORY",
)
EVENTS = 10_000
CLIENTS = 16
DAY = 86_400
TEST_ID = uuid4()
SCENARIOS = (
    ("uniform", datetime(2001, 1, 1, 12, tzinfo=UTC), TYPES),
    ("hot", datetime(2001, 1, 2, 12, tzinfo=UTC), TYPES[:1]),
)

session = get_cassandra_session()
try:
    delete = session.prepare(
        "DELETE FROM events_by_type WHERE event_type = ? AND bucket = ?"
    )
    delete.consistency_level = ConsistencyLevel.ALL
    for _, timestamp, types in SCENARIOS:
        for kind in types:
            session.execute(delete, (kind, int(timestamp.timestamp()) // DAY))

    insert = session.prepare(
        "INSERT INTO events_by_type "
        "(event_type, bucket, event_id, entity_type, entity_id, user_id, timestamp, details) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    )

    def write(params):
        started = perf_counter()
        try:
            session.execute(insert, params)
        except (DriverException, NoHostAvailable) as error:
            return params[0], None, type(error).__name__
        return params[0], (perf_counter() - started) * 1000, None

    output = csv.writer(sys.stdout, lineterminator="\n")
    output.writerow([
        "scenario", "bucket", "attempts", "clients", "success", "errors",
        "active_partitions", "top_partition_writes", "top_partition_pct",
        "throughput_ops_s", "mean_ms", "p95_ms",
    ])

    scenarios = reversed(SCENARIOS) if sys.argv[1:] == ["hot-first"] else SCENARIOS
    for scenario, timestamp, types in scenarios:
        bucket = int(timestamp.timestamp()) // DAY
        rows = [
            (types[i % len(types)], bucket, uuid_from_time(timestamp, clock_seq=i),
             "PRODUCT", TEST_ID, TEST_ID, timestamp, "{}")
            for i in range(EVENTS)
        ]

        started = perf_counter()
        with ThreadPoolExecutor(max_workers=CLIENTS) as workers:
            results = list(workers.map(write, rows))
        elapsed = perf_counter() - started

        counts = Counter(kind for kind, ms, _ in results if ms is not None)
        errors = Counter(error for _, _, error in results if error is not None)
        times = sorted(ms for _, ms, _ in results if ms is not None)
        top = max(counts.values(), default=0)
        output.writerow([
            scenario, bucket, EVENTS, CLIENTS, len(times), dict(errors) if errors else "",
            len(counts), top, round(100 * top / len(times), 2) if times else "",
            round(len(times) / elapsed, 2),
            round(mean(times), 3) if times else "",
            round(times[ceil(0.95 * len(times)) - 1], 3) if times else "",
        ])
finally:
    session.cluster.shutdown()
