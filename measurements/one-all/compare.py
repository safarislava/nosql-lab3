"""Compare Cassandra consistency levels on the prepared product history."""

import csv
import sys
from collections import Counter
from datetime import UTC, datetime
from math import ceil
from statistics import mean
from time import perf_counter

from cassandra import ConsistencyLevel, DriverException
from cassandra.cluster import EXEC_PROFILE_DEFAULT, NoHostAvailable

from domain.history import OperationEvent, OperationType
from infrastructure.environment.settings import settings
from infrastructure.persistence.cassandra.connection import get_cassandra_session
from infrastructure.persistence.cassandra.history_repository import CassandraHistoryRepository


levels = sys.argv[1:] or ["ONE", "QUORUM", "ALL"]
session = get_cassandra_session()
try:
    config = settings.cassandra
    history = CassandraHistoryRepository(
        session, config.bucket_seconds_type, config.bucket_seconds_entity,
        config.bucket_seconds_user,
    )
    profile = session.get_execution_profile(EXEC_PROFILE_DEFAULT)
    action = OperationType.UPDATE_PRODUCT

    def read():
        return history.get_events_by_type(
            action, datetime(2000, 1, 1, 12, tzinfo=UTC),
            datetime(2000, 1, 1, 12, 1, tzinfo=UTC), limit=20,
        )

    profile.consistency_level = ConsistencyLevel.ONE
    seed = read()
    if len(seed) != 20:
        sys.exit("Expected 20 prepared events in Cassandra.")

    def write():
        history.add_event(OperationEvent(
            user_id=seed[0].user_id, target_id=seed[0].target_id, action=action,
        ))

    results = csv.writer(sys.stdout)
    results.writerow(["level", "operation", "success_pct", "mean_ms", "p95_ms", "errors"])
    for level in levels:
        profile.consistency_level = ConsistencyLevel.name_to_value[level]
        for operation in (read, write):
            times = []
            errors = Counter()
            for attempt in range(105):
                started = perf_counter()
                try:
                    operation()
                except (DriverException, NoHostAvailable) as error:
                    if attempt >= 5:
                        name = type(error).__name__
                        if isinstance(error, NoHostAvailable):
                            causes = sorted({type(cause).__name__ for cause in error.errors.values()})
                            name += "(" + ", ".join(causes) + ")"
                        errors[name] += 1
                else:
                    if attempt >= 5:
                        times.append((perf_counter() - started) * 1000)

            times.sort()
            results.writerow([
                level, operation.__name__, len(times),
                round(mean(times), 3) if times else "",
                round(times[ceil(0.95 * len(times)) - 1], 3) if times else "",
                dict(errors) if errors else "",
            ])
finally:
    session.cluster.shutdown()
