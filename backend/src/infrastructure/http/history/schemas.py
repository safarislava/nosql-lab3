from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from application.history.dto import (
    OperationEventResponseDto,
    OrderHistoryResponseDto,
    ProductHistoryResponseDto,
    UserHistoryResponseDto,
)
from domain.history import OperationType


class OperationEventResponse(BaseModel):
    id: UUID
    user_id: UUID
    action: OperationType
    target_id: UUID | None = None
    details: dict[str, Any] = {}
    timestamp: datetime

    @classmethod
    def from_dto(cls, dto: OperationEventResponseDto) -> "OperationEventResponse":
        return cls(
            id=dto.id,
            user_id=dto.user_id,
            action=dto.action,
            target_id=dto.target_id,
            details=dto.details,
            timestamp=dto.timestamp,
        )


class UserHistoryResponse(BaseModel):
    user_id: UUID
    events: list[OperationEventResponse]
    limit: int = 20
    next_cursor: UUID | None = None

    @classmethod
    def from_dto(cls, dto: UserHistoryResponseDto) -> "UserHistoryResponse":
        return cls(
            user_id=dto.user_id,
            events=[OperationEventResponse.from_dto(e) for e in dto.events],
            limit=dto.limit,
            next_cursor=dto.next_cursor,
        )


class ProductHistoryResponse(BaseModel):
    product_id: UUID
    events: list[OperationEventResponse]
    limit: int = 20
    next_cursor: UUID | None = None

    @classmethod
    def from_dto(cls, dto: ProductHistoryResponseDto) -> "ProductHistoryResponse":
        return cls(
            product_id=dto.product_id,
            events=[OperationEventResponse.from_dto(e) for e in dto.events],
            limit=dto.limit,
            next_cursor=dto.next_cursor,
        )


class OrderHistoryResponse(BaseModel):
    order_id: UUID
    events: list[OperationEventResponse]
    limit: int = 20
    next_cursor: UUID | None = None

    @classmethod
    def from_dto(cls, dto: OrderHistoryResponseDto) -> "OrderHistoryResponse":
        return cls(
            order_id=dto.order_id,
            events=[OperationEventResponse.from_dto(e) for e in dto.events],
            limit=dto.limit,
            next_cursor=dto.next_cursor,
        )
