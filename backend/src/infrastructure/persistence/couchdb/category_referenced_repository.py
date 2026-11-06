from __future__ import annotations

import builtins
import logging
import re
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from application.category.repository import ICategoryRepository
from application.product.exceptions import ProductNotFoundException
from domain.category import Category
from infrastructure.environment.settings import settings
from infrastructure.persistence.couchdb.category_mapper import (
    CategoryCouchDbMapper,
)
from infrastructure.persistence.couchdb.client import CouchDbClient
from infrastructure.persistence.couchdb.exceptions import CouchDbConflictException

logger = logging.getLogger(__name__)


class CouchDbReferencedCategoryRepository(ICategoryRepository):
    """Репозиторий категорий (ссылки category_ids + база categories)."""

    def __init__(
        self,
        client: CouchDbClient,
    ) -> None:
        self._client = client
        self._products_db = settings.couchdb.products_db
        self._categories_db = settings.couchdb.categories_db
        self._ensure_dbs_initialized()

    def _ensure_dbs_initialized(self) -> None:
        """Гарантировать существование баз данных товаров и категорий."""
        try:
            self._client.ensure_database(self._products_db)
            self._client.ensure_database(self._categories_db)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Не удалось инициализировать базы CouchDB: %s", exc)

    def get_by_id(self, product_id: UUID, category_id: UUID) -> Category | None:
        """Получить категорию товара по ID."""
        doc = self._client.get_doc(self._products_db, str(product_id))
        if not doc or doc.get("type") != "product":
            return None

        cat_id_str = str(category_id)
        if cat_id_str not in doc.get("category_ids", []):
            return None

        cat_doc = self._client.get_doc(self._categories_db, cat_id_str)
        if cat_doc and cat_doc.get("type") == "category":
            return CategoryCouchDbMapper.from_dict(cat_doc)

        return None

    def list(self, product_id: UUID) -> builtins.list[Category]:
        """Получить список всех категорий товара."""
        doc = self._client.get_doc(self._products_db, str(product_id))
        if not doc or doc.get("type") != "product":
            return []

        cids = [str(cid) for cid in doc.get("category_ids", []) if cid]
        if not cids:
            return []

        query = CategoryCouchDbMapper.find_by_ids_query(cids)
        docs = self._client.find(self._categories_db, query)
        return [CategoryCouchDbMapper.from_dict(d) for d in docs]

    def _get_all_category_docs(self) -> builtins.list[dict[str, Any]]:
        """Получить все документы категорий из базы categories."""
        try:
            rows = self._client.get_all_docs(self._categories_db, include_docs=True)
            return [
                r["doc"]
                for r in rows
                if isinstance(r, dict)
                and isinstance(r.get("doc"), dict)
                and r["doc"].get("type") == "category"
            ]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Не удалось загрузить документы категорий: %s", exc)
            return []

    def _find_matching_category(
        self,
        category: Category,
        all_categories: builtins.list[dict[str, Any]],
    ) -> UUID | None:
        """Найти подходящую существующую категорию по id, slug или имени."""
        cat_id_str = str(category.id) if getattr(category, "id", None) else None
        target_slug = category.slug.strip().lower() if category.slug else ""
        target_name = category.name.strip().lower() if category.name else ""

        for doc in all_categories:
            doc_id = str(doc.get("_id", ""))
            if not doc_id:
                continue

            # 1. По точному совпадению ID
            if cat_id_str and doc_id == cat_id_str:
                return UUID(doc_id)

            # 2. По slug (если задан)
            doc_slug = str(doc.get("slug", "")).strip().lower()
            if target_slug and doc_slug and doc_slug == target_slug:
                return UUID(doc_id)

            # 3. По названию категории (без учета регистра)
            doc_name = str(doc.get("name", "")).strip().lower()
            if target_name and doc_name and doc_name == target_name:
                return UUID(doc_id)

        return None

    def add(self, product_id: UUID, category: Category) -> Category:
        """Добавить категорию и привязать к товару.
        Если подходящая категория уже есть, использовать её повторно без дублирования.
        """
        all_cat_docs = self._get_all_category_docs()
        matched_id = self._find_matching_category(category, all_cat_docs)

        if matched_id is not None:
            cat_id_str = str(matched_id)
            matched_doc = next(
                (d for d in all_cat_docs if str(d.get("_id")) == cat_id_str), None
            )
            if matched_doc:
                category = CategoryCouchDbMapper.from_dict(matched_doc)
        else:
            cat_id_str = str(category.id)
            self._client.mutate_doc(
                self._categories_db,
                cat_id_str,
                CategoryCouchDbMapper.mutator(category),
                create_if_missing=True,
            )

        def mutator(doc: dict[str, Any]) -> bool:
            if doc.get("type") != "product":
                return False
            cids = doc.setdefault("category_ids", [])
            if cat_id_str not in cids:
                cids.append(cat_id_str)
            return True

        if not self._client.mutate_doc(self._products_db, str(product_id), mutator):
            raise ProductNotFoundException(product_id)

        return category

    def update(self, product_id: UUID, category: Category) -> Category | None:
        """Обновить существующую категорию товара."""
        doc = self._client.get_doc(self._products_db, str(product_id))
        if not doc or doc.get("type") != "product":
            return None

        cat_id_str = str(category.id)
        if cat_id_str not in doc.get("category_ids", []):
            return None

        if not self._client.mutate_doc(
            self._categories_db, cat_id_str, CategoryCouchDbMapper.mutator(category)
        ):
            return None

        return category

    def delete(self, product_id: UUID, category_id: UUID) -> bool:
        """Отвязать категорию от товара по ID."""
        cat_id_str = str(category_id)

        def mutator(doc: dict[str, Any]) -> bool:
            if doc.get("type") != "product":
                return False
            cids = doc.get("category_ids", [])
            if cat_id_str not in cids:
                return False

            cids.remove(cat_id_str)
            doc["category_ids"] = cids
            return True

        return self._client.mutate_doc(self._products_db, str(product_id), mutator)

    def _find_existing_ids(self, ids: Sequence[UUID | str]) -> set[str]:
        """Получить множество существующих строковых _id категорий."""
        if not ids:
            return set()
        query = CategoryCouchDbMapper.find_by_ids_query(ids)
        return {
            str(doc["_id"])
            for doc in self._client.find(self._categories_db, query)
            if "_id" in doc
        }

    def save_missing_categories(
        self,
        categories: builtins.list[Category],
    ) -> builtins.list[UUID]:
        """Обработать категории для v2:
        - если подходящая категория уже есть в categories_db (по id, slug или имени),
          она используется повторно без создания дубликата;
        - если категории нет в базе, она создается в categories_db с данными из запроса;
        - идентификаторы категорий возвращаются для прикрепления к товару.
        """
        if not categories:
            return []

        all_cat_docs = self._get_all_category_docs()
        resolved_ids: builtins.list[UUID] = []

        for cat in categories:
            matched_id = self._find_matching_category(cat, all_cat_docs)
            if matched_id is not None:
                if matched_id not in resolved_ids:
                    resolved_ids.append(matched_id)
            else:
                cat_id_str = str(cat.id)
                existing = self._client.get_doc(self._categories_db, cat_id_str)
                if existing:
                    all_cat_docs.append(existing)
                    if cat.id not in resolved_ids:
                        resolved_ids.append(cat.id)
                    continue

                new_doc = CategoryCouchDbMapper.to_dict(cat)
                try:
                    self._client.save_doc(
                        self._categories_db,
                        new_doc,
                    )
                except CouchDbConflictException:
                    pass
                all_cat_docs.append(new_doc)
                if cat.id not in resolved_ids:
                    resolved_ids.append(cat.id)

        return resolved_ids

    def filter_existing_category_ids(
        self,
        category_ids: builtins.list[UUID],
    ) -> builtins.list[UUID]:
        """Оставить только существующие в categories_db ID категорий (батч-запрос)."""
        existing_ids = self._find_existing_ids(category_ids)
        return [cid for cid in category_ids if str(cid) in existing_ids]

    def search(
        self,
        query: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> builtins.list[Category]:
        """Поиск категорий по имени в categories_db."""
        selector: dict[str, Any] = {"type": "category"}
        if query and query.strip():
            escaped = re.escape(query.strip())
            selector["name"] = {"$regex": f"(?i){escaped}"}

        find_query: dict[str, Any] = {
            "selector": selector,
            "skip": offset,
            "limit": limit,
        }
        docs = self._client.find(self._categories_db, find_query)
        return [CategoryCouchDbMapper.from_dict(d) for d in docs]
