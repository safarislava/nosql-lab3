from functools import cache
from typing import Annotated

from application.recovery.repository import IRecoveryTokenRepository
from application.recovery.service import RecoveryService
from fastapi import Depends

from infrastructure.event_bus.dependencies import EventBusDep
from infrastructure.http.user.dependencies import UserServiceDep
from infrastructure.persistence.riak.recovery_token_repository import (
    RiakRecoveryTokenRepository,
)


@cache
def get_recovery_token_repository() -> IRecoveryTokenRepository:
    return RiakRecoveryTokenRepository()


RecoveryTokenRepositoryDep = Annotated[
    IRecoveryTokenRepository, Depends(get_recovery_token_repository)
]


def get_recovery_service(
    recovery_token_repository: RecoveryTokenRepositoryDep,
    user_service: UserServiceDep,
    event_bus: EventBusDep,
) -> RecoveryService:
    return RecoveryService(
        recovery_token_repository=recovery_token_repository,
        user_service=user_service,
        event_bus=event_bus,
    )


RecoveryServiceDep = Annotated[RecoveryService, Depends(get_recovery_service)]
