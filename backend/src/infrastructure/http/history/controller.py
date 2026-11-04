from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from domain.user import UserRole
from infrastructure.http.auth.dependencies import require_roles
from infrastructure.http.middleware.authentication_middleware import CurrentUserDep

from .dependencies import HistoryServiceDep
from .schemas import (
    OrderHistoryResponse,
    ProductHistoryResponse,
    UserHistoryResponse,
)

router = APIRouter(tags=["History"])


def _get_history(
    user_id: UUID,
    service: HistoryServiceDep,
    limit: int,
    last_event_id: UUID | None = None,
) -> UserHistoryResponse:
    dto = service.get_by_user_id(
        user_id=user_id,
        limit=limit,
        last_event_id=last_event_id,
    )
    return UserHistoryResponse.from_dto(dto)


@router.get(
    "/users/me/history",
    dependencies=[require_roles()],
    response_model=UserHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить историю действий текущего пользователя",
)
def get_user_history_me(
    current_user: CurrentUserDep,
    service: HistoryServiceDep,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Количество событий на страницу (limit)"),
    ] = 20,
    last_event_id: Annotated[
        UUID | None,
        Query(description="Курсор последнего события (event_id)"),
    ] = None,
) -> UserHistoryResponse:
    return _get_history(
        user_id=current_user.id,
        service=service,
        limit=limit,
        last_event_id=last_event_id,
    )


@router.get(
    "/users/{user_id}/history",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=UserHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить историю действий пользователя по ID (Admin)",
)
def get_user_history_by_user_id(
    user_id: UUID,
    service: HistoryServiceDep,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Количество событий на страницу (limit)"),
    ] = 20,
    last_event_id: Annotated[
        UUID | None,
        Query(description="Курсор последнего события (event_id)"),
    ] = None,
) -> UserHistoryResponse:
    return _get_history(
        user_id=user_id,
        service=service,
        limit=limit,
        last_event_id=last_event_id,
    )


@router.get(
    "/products/{product_id}/history",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=ProductHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить историю операций над товаром по ID (Admin)",
)
def get_product_history(
    product_id: UUID,
    service: HistoryServiceDep,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Количество событий на страницу (limit)"),
    ] = 20,
    last_event_id: Annotated[
        UUID | None,
        Query(description="Курсор последнего события (event_id)"),
    ] = None,
) -> ProductHistoryResponse:
    dto = service.get_by_product_id(
        product_id=product_id,
        limit=limit,
        last_event_id=last_event_id,
    )
    return ProductHistoryResponse.from_dto(dto)


@router.get(
    "/orders/{order_id}/history",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=OrderHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить историю операций над заказом по ID (Admin)",
)
def get_order_history(
    order_id: UUID,
    service: HistoryServiceDep,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Количество событий на страницу (limit)"),
    ] = 20,
    last_event_id: Annotated[
        UUID | None,
        Query(description="Курсор последнего события (event_id)"),
    ] = None,
) -> OrderHistoryResponse:
    dto = service.get_by_order_id(
        order_id=order_id,
        limit=limit,
        last_event_id=last_event_id,
    )
    return OrderHistoryResponse.from_dto(dto)
