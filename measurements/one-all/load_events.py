"""Load the benchmark events from JSON on standard input."""

import json
import sys
from datetime import UTC, datetime
from uuid import UUID

from cassandra import ConsistencyLevel
from cassandra.cluster import EXEC_PROFILE_DEFAULT

from domain.history import OperationEvent, OperationType
from infrastructure.environment.settings import settings
from infrastructure.persistence.cassandra.connection import get_cassandra_session
from infrastructure.persistence.cassandra.history_repository import (
    CassandraHistoryRepository,
)

events = json.load(sys.stdin)
session = get_cassandra_session()
try:
    session.get_execution_profile(EXEC_PROFILE_DEFAULT).consistency_level = (
        ConsistencyLevel.ALL
    )
    config = settings.cassandra
    history = CassandraHistoryRepository(
        session,
        config.bucket_seconds_type,
        config.bucket_seconds_entity,
        config.bucket_seconds_user,
    )
    for row in events:
        history.add_event(
            OperationEvent(
                id=UUID(row["id"]),
                user_id=UUID(row["user_id"]),
                target_id=UUID(row["target_id"]) if row["target_id"] else None,
                action=OperationType(row["action"]),
                details=row["details"],
                timestamp=datetime.fromisoformat(row["timestamp"]).replace(tzinfo=UTC),
            )
        )
finally:
    session.cluster.shutdown()

print(f"Loaded {len(events)} events.")
