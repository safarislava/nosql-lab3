from uuid import UUID

from application.event_bus import IEventBus
from application.session.service import SessionService
from application.user.exceptions import (
    InvalidCredentialsException,
    UserNotFoundException,
)
from application.user.hasher import IPasswordHasher
from application.user.service import UserService
from domain.history import OperationEvent, OperationType

from .dto import AuthResponseDto, LoginDto
from .token import ITokenService


class AuthService:
    def __init__(
        self,
        user_service: UserService,
        session_service: SessionService,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
        event_bus: IEventBus,
    ):
        self._user_service = user_service
        self._session_service = session_service
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._event_bus = event_bus

    def login(self, dto: LoginDto, ttl_days: int = 30) -> AuthResponseDto:
        user = None
        try:
            user = self._user_service.get_by_email(dto.email)
        except UserNotFoundException:
            self._event_bus.publish(
                OperationEvent(
                    user_id=UUID(int=0),
                    action=OperationType.LOGIN_FAILED,
                    details={"email": dto.email, "reason": "user_not_found"},
                )
            )
            raise InvalidCredentialsException()

        if not self._password_hasher.verify(dto.password, user.password_hash):
            self._event_bus.publish(
                OperationEvent(
                    user_id=user.id,
                    action=OperationType.LOGIN_FAILED,
                    details={"email": dto.email, "reason": "invalid_password"},
                )
            )
            raise InvalidCredentialsException()

        session_dto = self._session_service.create_session(
            user_id=user.id,
            ttl_days=ttl_days,
        )

        access_token = self._token_service.create_access_token(
            user_id=user.id,
            role=user.role,
        )

        self._event_bus.publish(
            OperationEvent(
                user_id=user.id,
                action=OperationType.USER_LOGIN,
                details={"email": user.email},
            )
        )

        return AuthResponseDto(
            user=user.to_response_dto(),
            session=session_dto,
            access_token=access_token,
        )

    def refresh(self, refresh_token: str, ttl_days: int = 30) -> AuthResponseDto:
        session_dto = self._session_service.refresh_session(
            refresh_token=refresh_token,
            ttl_days=ttl_days,
        )
        user_dto = self._user_service.get_by_id(session_dto.user_id)
        access_token = self._token_service.create_access_token(
            user_id=user_dto.id,
            role=user_dto.role,
        )

        return AuthResponseDto(
            user=user_dto,
            session=session_dto,
            access_token=access_token,
        )

    def logout_by_refresh_token(self, refresh_token: str) -> None:
        try:
            session = self._session_service.get_by_refresh_token(refresh_token)
            if session:
                self._event_bus.publish(
                    OperationEvent(
                        user_id=session.user_id,
                        action=OperationType.USER_LOGOUT,
                    )
                )
        except Exception:  # noqa: BLE001, S110
            pass
        self._session_service.delete_by_refresh_token(refresh_token)

    def logout_all(self, user_id: UUID) -> int:
        count = self._session_service.delete_all_user_sessions(user_id)
        self._event_bus.publish(
            OperationEvent(
                user_id=user_id,
                action=OperationType.USER_LOGOUT_ALL,
                details={"sessions_revoked": count},
            )
        )
        return count
