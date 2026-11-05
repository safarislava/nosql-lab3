from fastapi.testclient import TestClient

from domain.history import OperationEvent, OperationType
from domain.product import Product
from domain.user import User
from tests.conftest import RepositoriesContainer


class TestHistoryFunctional:
    """Функциональные тесты аудита и истории операций пользователя (основной и альтернативный потоки)."""

    # -----------------------------------------------------------------------
    # Основной поток (Happy Path)
    # -----------------------------------------------------------------------

    def test_history_records_events_and_get_me(
        self,
        client: TestClient,
        student_user: User,
        student_auth_headers: dict[str, str],
        sample_product: Product,
    ) -> None:
        """Основной поток: действия пользователя фиксируются в истории и доступны для чтения."""
        # Выполняем действия
        client.post(
            "/api/users/me/favourites",
            headers=student_auth_headers,
            json={"product_id": str(sample_product.id)},
        )
        client.patch(
            f"/api/users/me/cart/items/{sample_product.id}",
            headers=student_auth_headers,
            json={"quantity": 2},
        )

        # Запрашиваем историю
        response = client.get("/api/users/me/history", headers=student_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(student_user.id)
        events = data["events"]
        assert len(events) >= 2

        actions = [e["action"] for e in events]
        assert OperationType.ADD_FAVOURITE.value in actions
        assert OperationType.UPDATE_CART_ITEM.value in actions

    def test_history_pagination(
        self,
        client: TestClient,
        student_user: User,
        student_auth_headers: dict[str, str],
        repos: RepositoriesContainer,
    ) -> None:
        """Основной поток: курсорная пагинация по событиям истории (limit и last_event_id)."""
        # Наполняем историю событиями
        for i in range(5):
            repos.history_repo.add_event(
                OperationEvent(
                    user_id=student_user.id,
                    action=OperationType.ADD_CART_ITEM,
                    details={"index": i},
                )
            )

        # Запрашиваем первую страницу из 2 элементов
        page1 = client.get(
            "/api/users/me/history",
            headers=student_auth_headers,
            params={"limit": 2},
        )
        assert page1.status_code == 200
        data1 = page1.json()
        assert len(data1["events"]) == 2
        next_cursor = data1["next_cursor"]
        assert next_cursor is not None

        # Вторая страница через курсор
        page2 = client.get(
            "/api/users/me/history",
            headers=student_auth_headers,
            params={"limit": 2, "last_event_id": next_cursor},
        )
        assert page2.status_code == 200
        data2 = page2.json()
        assert len(data2["events"]) == 2
        ids1 = {e["id"] for e in data1["events"]}
        ids2 = {e["id"] for e in data2["events"]}
        assert not ids1.intersection(ids2)

    def test_admin_get_user_history_success(
        self,
        client: TestClient,
        student_user: User,
        admin_auth_headers: dict[str, str],
        repos: RepositoriesContainer,
    ) -> None:
        """Основной поток: администратор просматривает историю пользователя по ID."""
        repos.history_repo.add_event(
            OperationEvent(user_id=student_user.id, action=OperationType.USER_REGISTER)
        )

        # Админ читает историю студента
        get_resp = client.get(
            f"/api/users/{student_user.id}/history",
            headers=admin_auth_headers,
        )
        assert get_resp.status_code == 200
        assert len(get_resp.json()["events"]) >= 1

    # -----------------------------------------------------------------------
    # Альтернативные потоки (Alternative Flows & Errors)
    # -----------------------------------------------------------------------

    def test_get_history_me_unauthenticated(
        self,
        client: TestClient,
    ) -> None:
        """Альтернативный поток: запрос истории без авторизации -> 401."""
        response = client.get("/api/users/me/history")
        assert response.status_code == 401

    def test_get_history_by_user_id_forbidden_for_student(
        self,
        client: TestClient,
        student_auth_headers: dict[str, str],
        teacher_user: User,
    ) -> None:
        """Альтернативный поток: студент пытается посмотреть историю другого пользователя -> 403."""
        response = client.get(
            f"/api/users/{teacher_user.id}/history",
            headers=student_auth_headers,
        )
        assert response.status_code == 403

    def test_history_invalid_pagination(
        self,
        client: TestClient,
        student_auth_headers: dict[str, str],
    ) -> None:
        """Альтернативный поток: невалидный limit (0 или > 100) -> 422."""
        assert (
            client.get(
                "/api/users/me/history",
                headers=student_auth_headers,
                params={"limit": 0},
            ).status_code
            == 422
        )
        assert (
            client.get(
                "/api/users/me/history",
                headers=student_auth_headers,
                params={"limit": 500},
            ).status_code
            == 422
        )

    def test_admin_get_product_history_success(
        self,
        client: TestClient,
        sample_product: Product,
        admin_auth_headers: dict[str, str],
        student_auth_headers: dict[str, str],
        repos: RepositoriesContainer,
        admin_user: User,
    ) -> None:
        """Администратор получает историю товара, а студент получает 403."""
        repos.history_repo.add_event(
            OperationEvent(
                user_id=admin_user.id,
                action=OperationType.CREATE_PRODUCT,
                target_id=sample_product.id,
            )
        )

        # Студент -> 403
        student_resp = client.get(
            f"/api/products/{sample_product.id}/history",
            headers=student_auth_headers,
        )
        assert student_resp.status_code == 403

        # Неавторизованный -> 401
        anon_resp = client.get(f"/api/products/{sample_product.id}/history")
        assert anon_resp.status_code == 401

        # Админ -> 200
        admin_resp = client.get(
            f"/api/products/{sample_product.id}/history",
            headers=admin_auth_headers,
        )
        assert admin_resp.status_code == 200
        data = admin_resp.json()
        assert data["product_id"] == str(sample_product.id)
        assert "events" in data
        assert "next_cursor" in data

    def test_admin_get_order_history_success(
        self,
        client: TestClient,
        admin_auth_headers: dict[str, str],
        student_auth_headers: dict[str, str],
        repos: RepositoriesContainer,
        student_user: User,
    ) -> None:
        """Администратор получает историю заказа, а студент получает 403."""
        from uuid import uuid4

        order_id = uuid4()
        repos.history_repo.add_event(
            OperationEvent(
                user_id=student_user.id,
                action=OperationType.CREATE_ORDER,
                target_id=order_id,
            )
        )

        # Студент -> 403
        student_resp = client.get(
            f"/api/orders/{order_id}/history",
            headers=student_auth_headers,
        )
        assert student_resp.status_code == 403

        # Неавторизованный -> 401
        anon_resp = client.get(f"/api/orders/{order_id}/history")
        assert anon_resp.status_code == 401

        # Админ -> 200
        admin_resp = client.get(
            f"/api/orders/{order_id}/history",
            headers=admin_auth_headers,
        )
        assert admin_resp.status_code == 200
        data = admin_resp.json()
        assert data["order_id"] == str(order_id)
        assert "events" in data
        assert "next_cursor" in data

    def test_admin_get_events_by_type_success(
        self,
        client: TestClient,
        admin_auth_headers: dict[str, str],
        student_auth_headers: dict[str, str],
        repos: RepositoriesContainer,
        admin_user: User,
    ) -> None:
        """Администратор получает события по типу, а студент получает 403."""
        repos.history_repo.add_event(
            OperationEvent(
                user_id=admin_user.id,
                action=OperationType.CREATE_PRODUCT,
            )
        )

        # Студент -> 403
        student_resp = client.get(
            "/api/history",
            headers=student_auth_headers,
            params={"event_type": "CREATE_PRODUCT"},
        )
        assert student_resp.status_code == 403

        # Неавторизованный -> 401
        anon_resp = client.get("/api/history", params={"event_type": "CREATE_PRODUCT"})
        assert anon_resp.status_code == 401

        # Админ -> 200
        admin_resp = client.get(
            "/api/history",
            headers=admin_auth_headers,
            params={"event_type": "CREATE_PRODUCT", "limit": 10},
        )
        assert admin_resp.status_code == 200
        data = admin_resp.json()
        assert data["event_type"] == "CREATE_PRODUCT"
        assert len(data["events"]) >= 1

