import logging
from datetime import datetime
from uuid import UUID

from application.history.repository import IHistoryRepository
from domain.history import OperationEvent, OperationType
from infrastructure.persistence.cassandra.history_repository import (
    CassandraHistoryRepository,
)
from infrastructure.persistence.riak.history_cache_repository import (
    RiakHistoryCacheRepository,
)

logger = logging.getLogger(__name__)


class CompositeHistoryRepository(IHistoryRepository):
    """Композитный репозиторий истории операций с кэшированием в Riak KV (Cache-Aside) и персистентным хранением в Apache Cassandra."""

    def __init__(
        self,
        riak_repo: RiakHistoryCacheRepository,
        cassandra_repo: CassandraHistoryRepository,
        cache_capacity: int = 20,
    ) -> None:
        self._riak_repo = riak_repo
        self._cassandra_repo = cassandra_repo
        self._cache_capacity = cache_capacity

    def add_event(self, event: OperationEvent) -> None:
        """Сохраняет событие в персистентное хранилище Cassandra и инвалидирует кэш в Riak."""
        self._cassandra_repo.add_event(event)
        try:
            self._riak_repo.clear(event.user_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to invalidate history cache for user %s: %s", event.user_id, exc
            )

    def get_user_events(
        self,
        user_id: UUID,
        limit: int = 20,
        last_event_id: UUID | None = None,
    ) -> list[OperationEvent]:
        """Получить события пользователя из кэша Riak или персистентного хранилища Cassandra."""
        if last_event_id is None and limit <= self._cache_capacity:
            try:
                cached = self._riak_repo.get_cached_events(user_id, limit=limit)
                if cached is not None:
                    return cached
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to read history cache for user %s: %s", user_id, exc
                )

        events = self._cassandra_repo.get_user_events(
            user_id,
            limit=limit,
            last_event_id=last_event_id,
        )
        if last_event_id is None and events:
            try:
                self._riak_repo.set_cached_events(user_id, events)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to update history cache for user %s: %s", user_id, exc
                )
        return events

    def get_events_by_type(
        self,
        event_type: str | OperationType,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 50,
        last_event_id: UUID | None = None,
    ) -> list[OperationEvent]:
        """Запрос событий заданного типа за определенный период времени из Cassandra."""
        return self._cassandra_repo.get_events_by_type(
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            last_event_id=last_event_id,
        )

    def get_events_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        limit: int = 50,
        last_event_id: UUID | None = None,
    ) -> list[OperationEvent]:
        """Получить историю событий для конкретной сущности из Cassandra."""
        return self._cassandra_repo.get_events_by_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            last_event_id=last_event_id,
        )
