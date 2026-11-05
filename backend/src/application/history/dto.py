from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from domain.history import OperationEvent, OperationType, UserHistory


@dataclass(frozen=True)
class OperationEventResponseDto:
    id: UUID
    user_id: UUID
    action: OperationType
    target_id: UUID | None
    details: dict[str, Any]
    timestamp: datetime

    @classmethod
    def from_domain(cls, event: OperationEvent) -> "OperationEventResponseDto":
        return cls(
            id=event.id,
            user_id=event.user_id,
            action=event.action,
            target_id=event.target_id,
            details=event.details,
            timestamp=event.timestamp,
        )


@dataclass(frozen=True)
class UserHistoryResponseDto:
    user_id: UUID
    events: list[OperationEventResponseDto]
    limit: int
    next_cursor: UUID | None = None

    @classmethod
    def from_domain(
        cls,
        history: UserHistory,
        limit: int = 20,
    ) -> "UserHistoryResponseDto":
        all_events = history.get_recent_events(limit=limit)
        return cls.from_events(
            user_id=history.user_id,
            events=all_events,
            limit=limit,
        )

    @classmethod
    def from_events(
        cls,
        user_id: UUID,
        events: list[OperationEvent],
        limit: int = 20,
    ) -> "UserHistoryResponseDto":
        next_cursor = events[-1].id if len(events) == limit else None
        return cls(
            user_id=user_id,
            events=[OperationEventResponseDto.from_domain(e) for e in events],
            limit=limit,
            next_cursor=next_cursor,
        )


@dataclass(frozen=True)
class ProductHistoryResponseDto:
    product_id: UUID
    events: list[OperationEventResponseDto]
    limit: int
    next_cursor: UUID | None = None

    @classmethod
    def from_events(
        cls,
        product_id: UUID,
        events: list[OperationEvent],
        limit: int = 20,
    ) -> "ProductHistoryResponseDto":
        next_cursor = events[-1].id if len(events) == limit else None
        return cls(
            product_id=product_id,
            events=[OperationEventResponseDto.from_domain(e) for e in events],
            limit=limit,
            next_cursor=next_cursor,
        )


@dataclass(frozen=True)
class OrderHistoryResponseDto:
    order_id: UUID
    events: list[OperationEventResponseDto]
    limit: int
    next_cursor: UUID | None = None

    @classmethod
    def from_events(
        cls,
        order_id: UUID,
        events: list[OperationEvent],
        limit: int = 20,
    ) -> "OrderHistoryResponseDto":
        next_cursor = events[-1].id if len(events) == limit else None
        return cls(
            order_id=order_id,
            events=[OperationEventResponseDto.from_domain(e) for e in events],
            limit=limit,
            next_cursor=next_cursor,
        )


@dataclass(frozen=True)
class EventsByTypeResponseDto:
    event_type: OperationType
    events: list[OperationEventResponseDto]
    limit: int
    next_cursor: UUID | None = None

    @classmethod
    def from_events(
        cls,
        event_type: OperationType,
        events: list[OperationEvent],
        limit: int = 50,
    ) -> "EventsByTypeResponseDto":
        next_cursor = events[-1].id if len(events) == limit else None
        return cls(
            event_type=event_type,
            events=[OperationEventResponseDto.from_domain(e) for e in events],
            limit=limit,
            next_cursor=next_cursor,
        )

