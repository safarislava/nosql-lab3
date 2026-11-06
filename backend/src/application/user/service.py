from uuid import UUID

from application.event_bus import IEventBus
from domain.history import OperationEvent, OperationType
from domain.user import User

from .dto import (
    ChangePasswordDto,
    UserRegisterDto,
    UserResponseDto,
    UserUpdateDto,
    UserWithPasswordDto,
)
from .exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    UserNotFoundException,
    WeakNewPasswordException,
    WeakPasswordException,
)
from .hasher import IPasswordHasher
from .repository import IUserRepository


class UserService:
    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: IPasswordHasher,
        event_bus: IEventBus,
    ):
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._event_bus = event_bus

    def register(self, dto: UserRegisterDto) -> UserResponseDto:
        normalized_email = dto.email.strip().lower()

        if len(dto.password) < 6:
            raise WeakPasswordException()

        if self._user_repository.exists_by_email(normalized_email):
            raise UserAlreadyExistsException(normalized_email)

        user = User(
            name=dto.name.strip(),
            email=normalized_email,
            password_hash=self._password_hasher.hash(dto.password),
            role=dto.role,
        )
        saved_user = self._user_repository.save(user)
        self._event_bus.publish(
            OperationEvent(
                user_id=saved_user.id,
                action=OperationType.USER_REGISTER,
                details={"email": saved_user.email},
            )
        )
        return UserResponseDto.from_domain(saved_user)

    def get_by_id(self, user_id: UUID) -> UserResponseDto:
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundException(user_id)
        return UserResponseDto.from_domain(user)

    def get_by_ids(self, user_ids: list[UUID]) -> dict[UUID, UserResponseDto]:
        if not user_ids:
            return {}
        users = self._user_repository.get_by_ids(user_ids)
        return {u.id: UserResponseDto.from_domain(u) for u in users}

    def exists_by_id(self, user_id: UUID) -> bool:
        return self._user_repository.exists_by_id(user_id)

    def ensure_exists(self, user_id: UUID) -> None:
        if not self._user_repository.exists_by_id(user_id):
            raise UserNotFoundException(user_id)

    def get_by_email(self, email: str) -> UserWithPasswordDto:
        normalized_email = email.strip().lower()
        user = self._user_repository.get_by_email(normalized_email)
        if user is None:
            raise UserNotFoundException(normalized_email)
        return UserWithPasswordDto.from_domain(user)

    def find_by_email(self, email: str) -> UserResponseDto:
        return self.get_by_email(email).to_response_dto()

    def update_profile(self, user_id: UUID, dto: UserUpdateDto) -> UserResponseDto:
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundException(user_id)

        if dto.email is not None:
            new_email = dto.email.strip().lower()
            if new_email != user.email:
                if self._user_repository.exists_by_email(new_email):
                    raise UserAlreadyExistsException(new_email)
                user.email = new_email

        if dto.name is not None:
            user.name = dto.name.strip()

        saved_user = self._user_repository.save(user)
        self._event_bus.publish(
            OperationEvent(
                user_id=user_id,
                action=OperationType.UPDATE_PROFILE,
                details={"name": saved_user.name, "email": saved_user.email},
            )
        )
        return UserResponseDto.from_domain(saved_user)

    def change_password(self, user_id: UUID, dto: ChangePasswordDto) -> None:
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundException(user_id)

        if not self._password_hasher.verify(dto.old_password, user.password_hash):
            raise InvalidCredentialsException()

        if len(dto.new_password) < 6:
            raise WeakNewPasswordException()

        user.password_hash = self._password_hasher.hash(dto.new_password)
        self._user_repository.save(user)

        self._event_bus.publish(
            OperationEvent(
                user_id=user_id,
                action=OperationType.CHANGE_PASSWORD,
            )
        )

    def reset_password(self, user_id: UUID, new_password: str) -> None:
        if len(new_password) < 6:
            raise WeakNewPasswordException()

        new_hash = self._password_hasher.hash(new_password)
        if not self._user_repository.update_password_hash(user_id, new_hash):
            raise UserNotFoundException(user_id)

        self._event_bus.publish(
            OperationEvent(
                user_id=user_id,
                action=OperationType.PASSWORD_RESET,
                details={"type": "reset_password_with_token"},
            )
        )

    def delete_user(self, user_id: UUID, actor_id: UUID) -> bool:
        if not self._user_repository.delete(user_id):
            raise UserNotFoundException(user_id)

        action = (
            OperationType.DELETE_ACCOUNT
            if actor_id == user_id
            else OperationType.ADMIN_DELETE_USER
        )
        self._event_bus.publish(
            OperationEvent(
                user_id=actor_id,
                action=action,
                target_id=user_id,
            )
        )
        return True
