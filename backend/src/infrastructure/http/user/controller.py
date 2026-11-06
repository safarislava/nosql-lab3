from typing import Annotated
from uuid import UUID

from domain.user import UserRole
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import EmailStr

from infrastructure.http.auth.dependencies import require_roles
from infrastructure.http.middleware.authentication_middleware import CurrentUserDep
from infrastructure.http.user.schemas import (
    ChangePasswordRequest,
    RegisterUserRequest,
    UpdateUserRequest,
    UserResponse,
)

from .dependencies import UserServiceDep

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
)
def register(
    request: RegisterUserRequest,
    service: UserServiceDep,
) -> UserResponse:
    user_dto = service.register(request.to_dto())
    return UserResponse.from_dto(user_dto)


@router.get(
    "/me",
    dependencies=[require_roles()],
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить профиль текущего пользователя",
)
def get_me(
    current_user: CurrentUserDep,
    service: UserServiceDep,
) -> UserResponse:
    user_dto = service.get_by_id(current_user.id)
    return UserResponse.from_dto(user_dto)


@router.get(
    "/by-email",
    dependencies=[require_roles(UserRole.ADMIN, UserRole.TEACHER)],
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Найти пользователя по email (Admin, Teacher)",
)
def get_by_email(
    email: Annotated[EmailStr, Query(description="Email пользователя")],
    current_user: CurrentUserDep,
    service: UserServiceDep,
) -> UserResponse:
    user_dto = service.find_by_email(str(email))
    if current_user.role == UserRole.TEACHER and user_dto.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден.",
        )
    return UserResponse.from_dto(user_dto)


@router.get(
    "/{user_id}",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить пользователя по ID (Admin)",
)
def get_by_id(
    user_id: UUID,
    service: UserServiceDep,
) -> UserResponse:
    user_dto = service.get_by_id(user_id)
    return UserResponse.from_dto(user_dto)


@router.patch(
    "/me",
    dependencies=[require_roles()],
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить профиль текущего пользователя",
)
def update_profile_me(
    request: UpdateUserRequest,
    current_user: CurrentUserDep,
    service: UserServiceDep,
) -> UserResponse:
    user_dto = service.update_profile(current_user.id, request.to_dto())
    return UserResponse.from_dto(user_dto)


@router.patch(
    "/{user_id}",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить профиль пользователя по ID (Admin)",
)
def update_profile(
    user_id: UUID,
    request: UpdateUserRequest,
    service: UserServiceDep,
) -> UserResponse:
    user_dto = service.update_profile(user_id, request.to_dto())
    return UserResponse.from_dto(user_dto)


@router.post(
    "/me/change-password",
    dependencies=[require_roles()],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Сменить пароль текущего пользователя",
)
def change_password_me(
    request: ChangePasswordRequest,
    current_user: CurrentUserDep,
    service: UserServiceDep,
) -> None:
    service.change_password(current_user.id, request.to_dto())


@router.post(
    "/{user_id}/change-password",
    dependencies=[require_roles(UserRole.ADMIN)],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Сменить пароль пользователя по ID (Admin)",
)
def change_password(
    user_id: UUID,
    request: ChangePasswordRequest,
    service: UserServiceDep,
) -> None:
    service.change_password(user_id, request.to_dto())


@router.delete(
    "/me",
    dependencies=[require_roles()],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить профиль текущего пользователя",
)
def delete_user_me(
    current_user: CurrentUserDep,
    service: UserServiceDep,
) -> None:
    service.delete_user(current_user.id, actor_id=current_user.id)


@router.delete(
    "/{user_id}",
    dependencies=[require_roles(UserRole.ADMIN)],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить пользователя по ID (Admin)",
)
def delete_user(
    user_id: UUID,
    current_user: CurrentUserDep,
    service: UserServiceDep,
) -> None:
    service.delete_user(user_id, actor_id=current_user.id)
