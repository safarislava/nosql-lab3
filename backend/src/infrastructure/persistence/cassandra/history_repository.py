import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from cassandra.cluster import Session
from cassandra.util import datetime_from_uuid1

from application.history.repository import IHistoryRepository
from domain.history import OperationEvent, OperationType

logger = logging.getLogger(__name__)

_ACTION_ENTITY_MAP: dict[OperationType, str] = {
    OperationType.CREATE_ORDER: "ORDER",
    OperationType.CANCEL_ORDER: "ORDER",
    OperationType.APPROVE_ORDER: "ORDER",
    OperationType.REJECT_ORDER: "ORDER",
    OperationType.CREATE_PRODUCT: "PRODUCT",
    OperationType.UPDATE_PRODUCT: "PRODUCT",
    OperationType.DELETE_PRODUCT: "PRODUCT",
    OperationType.RESERVE_STOCK: "PRODUCT",
    OperationType.RESTORE_STOCK: "PRODUCT",
    OperationType.ADD_FAVOURITE: "PRODUCT",
    OperationType.REMOVE_FAVOURITE: "PRODUCT",
    OperationType.CLEAR_FAVOURITES: "PRODUCT",
    OperationType.ADD_CART_ITEM: "CART",
    OperationType.UPDATE_CART_ITEM: "CART",
    OperationType.REMOVE_CART_ITEM: "CART",
    OperationType.CLEAR_CART: "CART",
    OperationType.CHECKOUT: "ORDER",
    OperationType.USER_REGISTER: "USER",
    OperationType.UPDATE_PROFILE: "USER",
    OperationType.CHANGE_PASSWORD: "USER",
    OperationType.PASSWORD_RESET: "USER",
    OperationType.ADD_STUDENT: "USER",
    OperationType.REMOVE_STUDENT: "USER",
    OperationType.USER_LOGIN: "USER",
    OperationType.LOGIN_FAILED: "USER",
    OperationType.USER_LOGOUT: "USER",
    OperationType.USER_LOGOUT_ALL: "USER",
    OperationType.REQUEST_PASSWORD_RESET: "USER",
    OperationType.DELETE_ACCOUNT: "USER",
    OperationType.ADMIN_DELETE_USER: "USER",
    OperationType.CHANGE_USER_ROLE: "USER",
    OperationType.CREATE_CATEGORY: "CATEGORY",
    OperationType.UPDATE_CATEGORY: "CATEGORY",
    OperationType.DELETE_CATEGORY: "CATEGORY",
    OperationType.ASSIGN_PRODUCT_CATEGORY: "PRODUCT",
    OperationType.REMOVE_PRODUCT_CATEGORY: "PRODUCT",
    OperationType.UPLOAD_ATTACHMENT: "PRODUCT",
    OperationType.UPDATE_ATTACHMENT: "PRODUCT",
    OperationType.DELETE_ATTACHMENT: "PRODUCT",
    OperationType.TEACHER_ADD_STUDENT_CART: "CART",
    OperationType.TEACHER_CREATE_STUDENT_ORDER: "ORDER",
    OperationType.COMPLETE_ORDER: "ORDER",
    OperationType.PAY_ORDER: "ORDER",
}


def _resolve_entity_type(action: OperationType) -> str:
    """Определить тип сущности по типу действия."""
    return _ACTION_ENTITY_MAP.get(action, "UNKNOWN")


def _get_val(row: Any, key: str) -> Any:
    """Извлечь значение поля из строки Cassandra (namedtuple или dict)."""
    if isinstance(row, dict):
        return row.get(key)
    return getattr(row, key, None)


def _extract_time_from_uuid1(u: UUID) -> datetime:
    """Извлечь временную метку UTC из TimeUUID."""
    return datetime_from_uuid1(u).replace(tzinfo=UTC)


class CassandraHistoryRepository(IHistoryRepository):
    """Репозиторий истории операций в Apache Cassandra с раздельным временным бакетированием и курсорной пагинацией."""

    def __init__(
        self,
        session: Session,
        bucket_seconds_type: int,
        bucket_seconds_entity: int,
        bucket_seconds_user: int,
        max_scan_buckets: int = 30,
    ) -> None:
        self._session = session
        self._bucket_seconds_type = bucket_seconds_type
        self._bucket_seconds_entity = bucket_seconds_entity
        self._bucket_seconds_user = bucket_seconds_user
        self._max_scan_buckets = max_scan_buckets
        self._stmt_cache: dict[str, Any] = {}

    def _execute(self, cql: str, params: tuple[Any, ...]) -> Any:
        """Подготовить и выполнить CQL-запрос с автоматическим кэшированием Prepared Statements."""
        stmt = self._stmt_cache.get(cql)
        if stmt is None:
            stmt = self._session.prepare(cql)
            self._stmt_cache[cql] = stmt
        return self._session.execute(stmt, params)

    def _execute_async(self, cql: str, params: tuple[Any, ...]) -> Any:
        """Подготовить и отправить асинхронный CQL-запрос."""
        stmt = self._stmt_cache.get(cql)
        if stmt is None:
            stmt = self._session.prepare(cql)
            self._stmt_cache[cql] = stmt
        return self._session.execute_async(stmt, params)

    def _get_type_bucket(self, dt: datetime) -> int:
        """Вычислить индекс временного бакета для таблицы events_by_type."""
        return int(dt.timestamp() // self._bucket_seconds_type)

    def _get_entity_bucket(self, dt: datetime) -> int:
        """Вычислить индекс временного бакета для таблицы events_by_entity."""
        return int(dt.timestamp() // self._bucket_seconds_entity)

    def _get_user_bucket(self, dt: datetime) -> int:
        """Вычислить индекс временного бакета для таблицы events_by_user."""
        return int(dt.timestamp() // self._bucket_seconds_user)

    def _row_to_event(self, row: Any) -> OperationEvent:
        details_raw = _get_val(row, "details")
        details_dict: dict[str, Any] = {}
        if details_raw:
            try:
                details_dict = json.loads(details_raw)
            except Exception:  # noqa: BLE001
                details_dict = {"raw": details_raw}

        event_type_raw = _get_val(row, "event_type")
        try:
            action = OperationType(event_type_raw)
        except ValueError:
            action = event_type_raw

        return OperationEvent(
            id=_get_val(row, "event_id"),
            user_id=_get_val(row, "user_id"),
            action=action,
            target_id=_get_val(row, "entity_id"),
            details=details_dict,
            timestamp=_get_val(row, "timestamp"),
        )

    def add_event(self, event: OperationEvent) -> None:
        """Зафиксировать событие параллельно в трех денормализованных таблицах."""
        event_type = (
            event.action.value
            if isinstance(event.action, OperationType)
            else str(event.action)
        )
        entity_type = _resolve_entity_type(event.action)
        entity_id = event.target_id or event.user_id

        type_bucket = self._get_type_bucket(event.timestamp)
        entity_bucket = self._get_entity_bucket(event.timestamp)
        user_bucket = self._get_user_bucket(event.timestamp)

        details_json = json.dumps(event.details, default=str)

        future_type = self._execute_async(
            """
            INSERT INTO events_by_type (
                event_type, bucket, event_id, entity_type, entity_id, user_id, timestamp, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_type,
                type_bucket,
                event.id,
                entity_type,
                entity_id,
                event.user_id,
                event.timestamp,
                details_json,
            ),
        )
        future_entity = self._execute_async(
            """
            INSERT INTO events_by_entity (
                entity_type, entity_id, bucket, event_id, event_type, user_id, timestamp, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entity_type,
                entity_id,
                entity_bucket,
                event.id,
                event_type,
                event.user_id,
                event.timestamp,
                details_json,
            ),
        )
        future_user = self._execute_async(
            """
            INSERT INTO events_by_user (
                user_id, bucket, event_id, event_type, entity_type, entity_id, timestamp, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.user_id,
                user_bucket,
                event.id,
                event_type,
                entity_type,
                entity_id,
                event.timestamp,
                details_json,
            ),
        )

        future_type.result()
        future_entity.result()
        future_user.result()

    def get_user_events(
        self,
        user_id: UUID,
        limit: int = 20,
        last_event_id: UUID | None = None,
    ) -> list[OperationEvent]:
        """Получить события пользователя с курсорной пагинацией по last_event_id."""
        events: list[OperationEvent] = []

        if last_event_id is not None:
            cursor_time = _extract_time_from_uuid1(last_event_id)
            start_b = self._get_user_bucket(cursor_time)
            first_is_cursor = True
        else:
            start_b = self._get_user_bucket(datetime.now(UTC))
            first_is_cursor = False

        for b in range(start_b, start_b - self._max_scan_buckets, -1):
            remaining = limit - len(events)
            if remaining <= 0:
                break

            if b == start_b and first_is_cursor:
                rows = self._execute(
                    """
                    SELECT user_id, bucket, event_id, event_type, entity_type, entity_id, timestamp, details
                    FROM events_by_user
                    WHERE user_id = ? AND bucket = ? AND event_id < ?
                    LIMIT ?
                    """,
                    (user_id, b, last_event_id, remaining),
                )
            else:
                rows = self._execute(
                    """
                    SELECT user_id, bucket, event_id, event_type, entity_type, entity_id, timestamp, details
                    FROM events_by_user
                    WHERE user_id = ? AND bucket = ?
                    LIMIT ?
                    """,
                    (user_id, b, remaining),
                )

            events.extend(self._row_to_event(r) for r in rows)

        return events[:limit]

    def get_events_by_type(
        self,
        event_type: str | OperationType,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 50,
        last_event_id: UUID | None = None,
    ) -> list[OperationEvent]:
        """Запрос событий заданного типа за определенный период времени с курсорной пагинацией."""
        type_str = (
            event_type.value
            if isinstance(event_type, OperationType)
            else str(event_type)
        )
        events: list[OperationEvent] = []

        if last_event_id is not None:
            cursor_time = _extract_time_from_uuid1(last_event_id)
            start_b = self._get_type_bucket(cursor_time)
            first_is_cursor = True
        else:
            ref_end = end_time if end_time is not None else datetime.now(UTC)
            start_b = self._get_type_bucket(ref_end)
            first_is_cursor = False

        min_b = (
            self._get_type_bucket(start_time)
            if start_time is not None
            else start_b - self._max_scan_buckets
        )

        for b in range(start_b, min_b - 1, -1):
            remaining = limit - len(events)
            if remaining <= 0:
                break

            conditions = ["event_type = ?", "bucket = ?"]
            params: list[Any] = [type_str, b]

            if start_time is not None:
                conditions.append("event_id >= minTimeuuid(?)")
                params.append(start_time)

            if b == start_b and first_is_cursor:
                conditions.append("event_id < ?")
                params.append(last_event_id)
            elif end_time is not None and b == self._get_type_bucket(end_time):
                conditions.append("event_id <= maxTimeuuid(?)")
                params.append(end_time)

            params.append(remaining)
            rows = self._execute(
                f"""
                SELECT event_type, bucket, event_id, entity_type, entity_id, user_id, timestamp, details
                FROM events_by_type
                WHERE {" AND ".join(conditions)}
                LIMIT ?
                """,
                tuple(params),
            )
            events.extend(self._row_to_event(r) for r in rows)

        return events[:limit]

    def get_events_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        limit: int = 50,
        last_event_id: UUID | None = None,
    ) -> list[OperationEvent]:
        """Получить историю событий для сущности с курсорной пагинацией по last_event_id."""
        events: list[OperationEvent] = []

        if last_event_id is not None:
            cursor_time = _extract_time_from_uuid1(last_event_id)
            start_b = self._get_entity_bucket(cursor_time)
            first_is_cursor = True
        else:
            start_b = self._get_entity_bucket(datetime.now(UTC))
            first_is_cursor = False

        for b in range(start_b, start_b - self._max_scan_buckets, -1):
            remaining = limit - len(events)
            if remaining <= 0:
                break

            if b == start_b and first_is_cursor:
                rows = self._execute(
                    """
                    SELECT entity_type, entity_id, bucket, event_id, event_type, user_id, timestamp, details
                    FROM events_by_entity
                    WHERE entity_type = ? AND entity_id = ? AND bucket = ? AND event_id < ?
                    LIMIT ?
                    """,
                    (entity_type, entity_id, b, last_event_id, remaining),
                )
            else:
                rows = self._execute(
                    """
                    SELECT entity_type, entity_id, bucket, event_id, event_type, user_id, timestamp, details
                    FROM events_by_entity
                    WHERE entity_type = ? AND entity_id = ? AND bucket = ?
                    LIMIT ?
                    """,
                    (entity_type, entity_id, b, remaining),
                )

            events.extend(self._row_to_event(r) for r in rows)

        return events[:limit]
