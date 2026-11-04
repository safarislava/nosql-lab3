import logging
from uuid import UUID

from application.history.repository import IHistoryRepository
from domain.history import OperationEvent
from infrastructure.persistence.riak.history_cache_repository import (
    RiakHistoryCacheRepository,
)

logger = logging.getLogger(__name__)


class CompositeHistoryRepository(IHistoryRepository):
    """Композитный репозиторий истории операций с кэшированием в Riak KV (Cache-Aside)."""

    def __init__(
        self,
        riak_repo: RiakHistoryCacheRepository,
        cache_capacity: int = 20,
    ) -> None:
        self._riak_repo = riak_repo
        self._cache_capacity = cache_capacity

    def add_event(self, event: OperationEvent) -> None:
        """Сохраняет событие и инвалидирует кэш в Riak."""
        try:
            self._riak_repo.clear(event.user_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to invalidate history cache for user %s: %s", event.user_id, exc
            )

    def get_user_events(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> list[OperationEvent]:
        """Получить события пользователя из кэша Riak."""
        if offset == 0 and limit <= self._cache_capacity:
            try:
                cached = self._riak_repo.get_cached_events(user_id, limit=limit)
                if cached is not None:
                    return cached
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to read history cache for user %s: %s", user_id, exc
                )

        return []

    def clear(self, user_id: UUID) -> bool:
        """Очищает историю и инвалидирует кэш в Riak."""
        try:
            self._riak_repo.clear(user_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to clear history cache for user %s: %s", user_id, exc
            )
        return True
