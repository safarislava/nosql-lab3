from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid1


class OperationType(StrEnum):
    ADD_FAVOURITE = "ADD_FAVOURITE"
    REMOVE_FAVOURITE = "REMOVE_FAVOURITE"
    CLEAR_FAVOURITES = "CLEAR_FAVOURITES"
    ADD_CART_ITEM = "ADD_CART_ITEM"
    UPDATE_CART_ITEM = "UPDATE_CART_ITEM"
    REMOVE_CART_ITEM = "REMOVE_CART_ITEM"
    CLEAR_CART = "CLEAR_CART"
    CREATE_ORDER = "CREATE_ORDER"
    CANCEL_ORDER = "CANCEL_ORDER"
    APPROVE_ORDER = "APPROVE_ORDER"
    REJECT_ORDER = "REJECT_ORDER"
    CREATE_PRODUCT = "CREATE_PRODUCT"
    UPDATE_PRODUCT = "UPDATE_PRODUCT"
    DELETE_PRODUCT = "DELETE_PRODUCT"
    RESERVE_STOCK = "RESERVE_STOCK"
    RESTORE_STOCK = "RESTORE_STOCK"
    CHECKOUT = "CHECKOUT"
    USER_REGISTER = "USER_REGISTER"
    UPDATE_PROFILE = "UPDATE_PROFILE"
    CHANGE_PASSWORD = "CHANGE_PASSWORD"
    PASSWORD_RESET = "PASSWORD_RESET"
    ADD_STUDENT = "ADD_STUDENT"
    REMOVE_STUDENT = "REMOVE_STUDENT"
    USER_LOGIN = "USER_LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    USER_LOGOUT = "USER_LOGOUT"
    USER_LOGOUT_ALL = "USER_LOGOUT_ALL"
    REQUEST_PASSWORD_RESET = "REQUEST_PASSWORD_RESET"
    DELETE_ACCOUNT = "DELETE_ACCOUNT"
    CREATE_CATEGORY = "CREATE_CATEGORY"
    UPDATE_CATEGORY = "UPDATE_CATEGORY"
    DELETE_CATEGORY = "DELETE_CATEGORY"
    ASSIGN_PRODUCT_CATEGORY = "ASSIGN_PRODUCT_CATEGORY"
    REMOVE_PRODUCT_CATEGORY = "REMOVE_PRODUCT_CATEGORY"
    UPLOAD_ATTACHMENT = "UPLOAD_ATTACHMENT"
    UPDATE_ATTACHMENT = "UPDATE_ATTACHMENT"
    DELETE_ATTACHMENT = "DELETE_ATTACHMENT"
    ADMIN_DELETE_USER = "ADMIN_DELETE_USER"


@dataclass
class OperationEvent:
    user_id: UUID
    action: OperationType
    target_id: UUID | None = None
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid1)


@dataclass
class UserHistory:
    user_id: UUID
    events: list[OperationEvent] = field(default_factory=list)

    def get_recent_events(self, limit: int = 10) -> list[OperationEvent]:
        return sorted(self.events, key=lambda e: e.timestamp, reverse=True)[:limit]
