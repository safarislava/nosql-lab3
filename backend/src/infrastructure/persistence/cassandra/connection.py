import logging
from functools import cache

from cassandra import ConsistencyLevel
from cassandra.cluster import (
    EXEC_PROFILE_DEFAULT,
    Cluster,
    ExecutionProfile,
    Session,
)

from infrastructure.environment.settings import settings

logger = logging.getLogger(__name__)


@cache
def get_cassandra_session() -> Session:
    """Синглтон сессии Cassandra."""
    consistency = getattr(
        ConsistencyLevel,
        settings.cassandra.consistency_level.upper(),
        ConsistencyLevel.QUORUM,
    )
    profile = ExecutionProfile(consistency_level=consistency)
    cluster = Cluster(
        contact_points=settings.cassandra.contact_points,
        port=settings.cassandra.port,
        execution_profiles={EXEC_PROFILE_DEFAULT: profile},
    )
    return cluster.connect(settings.cassandra.keyspace)


def close_cassandra_session() -> None:
    """Закрыть сессию и соединение с кластером Cassandra."""
    session = get_cassandra_session()
    session.shutdown()
    session.cluster.shutdown()
