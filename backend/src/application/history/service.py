from datetime import datetime
from uuid import UUID

from application.event_bus import IEventBus
from domain.history import OperationEvent, OperationType

from .dto import (
    OperationEventResponseDto,
    OrderHistoryResponseDto,
    ProductHistoryResponseDto,
    UserHistoryResponseDto,
)
from .repository import IHistoryRepository


class HistoryService:
    """Сервис истории действий пользователей."""

    def __init__(
        self,
        history_repository: IHistoryRepository,
        event_bus: IEventBus,
    ) -> None:
        self._history_repository = history_repository
        event_bus.subscribe(OperationEvent, self.handle_event)

    def handle_event(self, event: OperationEvent) -> None:
        """Обработчик события из шины событий."""
        self.record_event(event)

    def record_event(self, event: OperationEvent) -> None:
        """Зафиксировать событие в истории."""
        self._history_repository.add_event(event)

    def get_by_user_id(
        self,
        user_id: UUID,
        limit: int = 20,
        last_event_id: UUID | None = None,
    ) -> UserHistoryResponseDto:
        """Получить историю действий пользователя с курсорной пагинацией."""
        events = self._history_repository.get_user_events(
            user_id=user_id,
            limit=limit,
            last_event_id=last_event_id,
        )
        return UserHistoryResponseDto.from_events(
            user_id=user_id,
            events=events,
            limit=limit,
        )

    def get_events_by_type(
        self,
        event_type: str | OperationType,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 50,
        last_event_id: UUID | None = None,
    ) -> list[OperationEventResponseDto]:
        """Получить события заданного типа за определенный период времени."""
        events = self._history_repository.get_events_by_type(
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            last_event_id=last_event_id,
        )
        return [OperationEventResponseDto.from_domain(e) for e in events]

    def get_by_product_id(
        self,
        product_id: UUID,
        limit: int = 20,
        last_event_id: UUID | None = None,
    ) -> ProductHistoryResponseDto:
        """Получить историю операций над товаром с курсорной пагинацией."""
        events = self._history_repository.get_events_by_entity(
            entity_type="PRODUCT",
            entity_id=product_id,
            limit=limit,
            last_event_id=last_event_id,
        )
        return ProductHistoryResponseDto.from_events(
            product_id=product_id,
            events=events,
            limit=limit,
        )

    def get_by_order_id(
        self,
        order_id: UUID,
        limit: int = 20,
        last_event_id: UUID | None = None,
    ) -> OrderHistoryResponseDto:
        """Получить историю операций над заказом с курсорной пагинацией."""
        events = self._history_repository.get_events_by_entity(
            entity_type="ORDER",
            entity_id=order_id,
            limit=limit,
            last_event_id=last_event_id,
        )
        return OrderHistoryResponseDto.from_events(
            order_id=order_id,
            events=events,
            limit=limit,
        )
