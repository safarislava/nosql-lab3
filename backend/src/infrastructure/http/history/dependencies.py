from functools import cache
from typing import Annotated

from fastapi import Depends

from application.history.repository import IHistoryRepository
from application.history.service import HistoryService
from infrastructure.environment.settings import settings
from infrastructure.event_bus.dependencies import get_event_bus
from infrastructure.persistence.cassandra.connection import get_cassandra_session
from infrastructure.persistence.cassandra.history_repository import (
    CassandraHistoryRepository,
)
from infrastructure.persistence.composite.history_repository import (
    CompositeHistoryRepository,
)
from infrastructure.persistence.riak.history_cache_repository import (
    RiakHistoryCacheRepository,
)


@cache
def get_cassandra_history_repository() -> CassandraHistoryRepository:
    return CassandraHistoryRepository(
        session=get_cassandra_session(),
        bucket_seconds_type=settings.cassandra.bucket_seconds_type,
        bucket_seconds_entity=settings.cassandra.bucket_seconds_entity,
        bucket_seconds_user=settings.cassandra.bucket_seconds_user,
    )


@cache
def get_riak_history_cache_repository() -> RiakHistoryCacheRepository:
    return RiakHistoryCacheRepository()


@cache
def get_history_repository() -> IHistoryRepository:
    return CompositeHistoryRepository(
        riak_repo=get_riak_history_cache_repository(),
        cassandra_repo=get_cassandra_history_repository(),
    )


HistoryRepositoryDep = Annotated[IHistoryRepository, Depends(get_history_repository)]


@cache
def get_history_service() -> HistoryService:
    return HistoryService(
        history_repository=get_history_repository(),
        event_bus=get_event_bus(),
    )


HistoryServiceDep = Annotated[HistoryService, Depends(get_history_service)]
