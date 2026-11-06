import secrets
from datetime import UTC, datetime, timedelta

from application.event_bus import IEventBus
from application.user.service import UserService
from domain.history import OperationEvent, OperationType
from domain.recovery_token import RecoveryToken

from .dto import (
    CreateRecoveryDto,
    RecoveryResponseDto,
    ResetPasswordWithTokenDto,
)
from .exceptions import (
    RecoveryTokenExpiredException,
    RecoveryTokenNotFoundException,
)
from .repository import IRecoveryTokenRepository


class RecoveryService:
    def __init__(
        self,
        recovery_token_repository: IRecoveryTokenRepository,
        user_service: UserService,
        event_bus: IEventBus,
    ) -> None:
        self._recovery_token_repository = recovery_token_repository
        self._user_service = user_service
        self._event_bus = event_bus

    def create_token(
        self, dto: CreateRecoveryDto, ttl_minutes: int = 15
    ) -> RecoveryResponseDto:
        user = self._user_service.get_by_email(dto.email)
        expires_at = datetime.now(UTC) + timedelta(minutes=ttl_minutes)

        token = self._generate_unique_token()

        recovery_token = RecoveryToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
        )

        saved_token = self._recovery_token_repository.save(recovery_token)

        self._event_bus.publish(
            OperationEvent(
                user_id=user.id,
                action=OperationType.REQUEST_PASSWORD_RESET,
                details={"email": user.email},
            )
        )

        return RecoveryResponseDto.from_domain(saved_token)

    def _generate_unique_token(self) -> str:
        return secrets.token_urlsafe(32)

    def validate_token(self, token: str) -> RecoveryResponseDto:
        recovery_token = self._recovery_token_repository.get_by_token(token)
        if recovery_token is None:
            raise RecoveryTokenNotFoundException(token)

        if recovery_token.is_expired():
            self._recovery_token_repository.delete_by_token(token)
            raise RecoveryTokenExpiredException()

        return RecoveryResponseDto.from_domain(recovery_token)

    def reset_password(self, dto: ResetPasswordWithTokenDto) -> None:
        recovery_token = self.validate_token(dto.token)

        self._user_service.reset_password(
            user_id=recovery_token.user_id,
            new_password=dto.new_password,
        )

        self._recovery_token_repository.delete_by_token(dto.token)
