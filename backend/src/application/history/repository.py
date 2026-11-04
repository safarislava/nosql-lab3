from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from domain.history import OperationEvent, OperationType


class IHistoryRepository(ABC):
    """Интерфейс репозитория истории операций."""

    @abstractmethod
    def add_event(self, event: OperationEvent) -> None:
        """Зафиксировать событие в истории."""
        raise NotImplementedError

    @abstractmethod
    def get_user_events(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 20,
        last_event_id: UUID | None = None,
    ) -> list[OperationEvent]:
        """Получить события пользователя с пагинацией."""
        raise NotImplementedError

    @abstractmethod
    def get_events_by_type(
        self,
        event_type: str | OperationType,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 50,
        last_event_id: UUID | None = None,
    ) -> list[OperationEvent]:
        """Запрос событий заданного типа за определенный период времени."""
        raise NotImplementedError

    @abstractmethod
    def get_events_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 50,
        last_event_id: UUID | None = None,
    ) -> list[OperationEvent]:
        """Получить историю событий для конкретной сущности (Product, Order и др.)."""
        raise NotImplementedError
