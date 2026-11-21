from uuid import UUID

from fastapi import APIRouter, status

from application.order.exceptions import OrderNotFoundException
from domain.user import UserRole
from infrastructure.http.auth.dependencies import require_roles
from infrastructure.http.middleware.authentication_middleware import CurrentUserDep

from .dependencies import OrderServiceDep
from .schemas import (
    CreateOrderRequest,
    OrderFilterParams,
    OrderListResponse,
    OrderResponse,
    UserOrderFilterParams,
)

router = APIRouter(tags=["Orders"])


@router.post(
    "/users/me/orders/search",
    dependencies=[require_roles()],
    response_model=OrderListResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить список заказов текущего пользователя",
)
def list_my_orders(
    current_user: CurrentUserDep,
    service: OrderServiceDep,
    filters: UserOrderFilterParams | None = None,
) -> OrderListResponse:
    filter_params = filters or UserOrderFilterParams()
    result = service.list_user_orders(
        user_id=current_user.id,
        status=filter_params.status,
        offset=filter_params.offset,
        limit=filter_params.limit,
    )
    total_orders_count = service.get_user_orders_count(current_user.id)
    return OrderListResponse.from_dto(result, total_orders_count=total_orders_count)


@router.post(
    "/users/{user_id}/orders/search",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=OrderListResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить список заказов пользователя по ID (Admin)",
)
def list_orders_by_user_id(
    user_id: UUID,
    service: OrderServiceDep,
    filters: UserOrderFilterParams | None = None,
) -> OrderListResponse:
    filter_params = filters or UserOrderFilterParams()
    result = service.list_user_orders(
        user_id=user_id,
        status=filter_params.status,
        offset=filter_params.offset,
        limit=filter_params.limit,
    )
    total_orders_count = service.get_user_orders_count(user_id)
    return OrderListResponse.from_dto(result, total_orders_count=total_orders_count)


@router.post(
    "/users/me/orders",
    dependencies=[require_roles()],
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый заказ для текущего пользователя",
)
def create_order_me(
    request: CreateOrderRequest,
    current_user: CurrentUserDep,
    service: OrderServiceDep,
) -> OrderResponse:
    dto = service.create(
        user_id=current_user.id,
        dto=request.to_dto(),
    )
    return OrderResponse.from_dto(dto)


@router.post(
    "/users/{user_id}/orders",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый заказ для пользователя по ID (Admin)",
)
def create_order_by_user_id(
    user_id: UUID,
    request: CreateOrderRequest,
    service: OrderServiceDep,
) -> OrderResponse:
    dto = service.create(
        user_id=user_id,
        dto=request.to_dto(),
    )
    return OrderResponse.from_dto(dto)


@router.get(
    "/users/me/orders/{order_id}",
    dependencies=[require_roles()],
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить информацию о заказе текущего пользователя по ID",
)
def get_order_me(
    order_id: UUID,
    current_user: CurrentUserDep,
    service: OrderServiceDep,
) -> OrderResponse:
    dto = service.get_by_id(order_id)
    if dto.user_id != current_user.id:
        raise OrderNotFoundException(order_id)
    return OrderResponse.from_dto(dto)


@router.post(
    "/users/me/orders/{order_id}/cancel",
    dependencies=[require_roles()],
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Отменить заказ текущего пользователя (пока он не одобрен)",
)
def cancel_order_me_post(
    order_id: UUID,
    current_user: CurrentUserDep,
    service: OrderServiceDep,
) -> OrderResponse:
    dto = service.get_by_id(order_id)
    if dto.user_id != current_user.id:
        raise OrderNotFoundException(order_id)
    cancelled = service.cancel(current_user.id, order_id)
    return OrderResponse.from_dto(cancelled)


@router.get(
    "/users/{user_id}/orders/{order_id}",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить информацию о заказе пользователя по ID (Admin)",
)
def get_order_by_user_id(
    user_id: UUID,
    order_id: UUID,
    service: OrderServiceDep,
) -> OrderResponse:
    dto = service.get_by_id(order_id)
    if dto.user_id != user_id:
        raise OrderNotFoundException(order_id)
    return OrderResponse.from_dto(dto)


@router.post(
    "/orders/search",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=OrderListResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить список заказов",
)
def list_orders(
    service: OrderServiceDep,
    filters: OrderFilterParams | None = None,
) -> OrderListResponse:
    filter_params = filters or OrderFilterParams()
    result = service.list(filter_params.to_dto())
    total_orders_count = (
        service.get_user_orders_count(filter_params.user_id)
        if filter_params.user_id is not None
        else service.get_total_orders_count()
    )
    return OrderListResponse.from_dto(result, total_orders_count=total_orders_count)


@router.get(
    "/orders/{order_id}",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить информацию о заказе по ID",
)
def get_order(
    order_id: UUID,
    service: OrderServiceDep,
) -> OrderResponse:
    dto = service.get_by_id(order_id)
    return OrderResponse.from_dto(dto)


@router.post(
    "/orders/{order_id}/cancel",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Отменить заказ",
)
def cancel_order(
    order_id: UUID,
    current_user: CurrentUserDep,
    service: OrderServiceDep,
) -> OrderResponse:
    dto = service.cancel(current_user.id, order_id)
    return OrderResponse.from_dto(dto)


@router.post(
    "/orders/{order_id}/approve",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Подтвердить заказ",
)
def approve_order(
    order_id: UUID,
    current_user: CurrentUserDep,
    service: OrderServiceDep,
) -> OrderResponse:
    dto = service.approve(current_user.id, order_id)
    return OrderResponse.from_dto(dto)


@router.post(
    "/orders/{order_id}/reject",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Отклонить заказ",
)
def reject_order(
    order_id: UUID,
    current_user: CurrentUserDep,
    service: OrderServiceDep,
) -> OrderResponse:
    dto = service.reject(current_user.id, order_id)
    return OrderResponse.from_dto(dto)
