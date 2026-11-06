from __future__ import annotations

from uuid import UUID

from domain.category import Category
from domain.history import OperationEvent, OperationType

from application.event_bus import IEventBus

from .dto import (
    CategoryCreateDto,
    CategoryListResponseDto,
    CategoryResponseDto,
    CategoryUpdateDto,
)
from .exceptions import (
    CategoryNotFoundException,
    EmptyCategoryNameException,
)
from .repository import ICategoryRepository


class CategoryService:
    def __init__(
        self,
        category_repository: ICategoryRepository,
        event_bus: IEventBus,
    ) -> None:
        self._category_repository = category_repository
        self._event_bus = event_bus

    def add_category(
        self, product_id: UUID, dto: CategoryCreateDto, user_id: UUID
    ) -> CategoryResponseDto:
        if not dto.name.strip():
            raise EmptyCategoryNameException()

        category = Category(
            name=dto.name.strip(),
            slug=dto.slug.strip(),
            description=dto.description.strip(),
        )
        saved = self._category_repository.add(product_id, category)
        self._event_bus.publish(
            OperationEvent(
                user_id=user_id,
                action=OperationType.CREATE_CATEGORY,
                target_id=saved.id,
                details={"product_id": str(product_id), "name": saved.name},
            )
        )
        return CategoryResponseDto.from_domain(saved)

    def get_by_id(self, product_id: UUID, category_id: UUID) -> CategoryResponseDto:
        category = self._category_repository.get_by_id(product_id, category_id)
        if category is None:
            raise CategoryNotFoundException(category_id)
        return CategoryResponseDto.from_domain(category)

    def list(self, product_id: UUID) -> CategoryListResponseDto:
        """Получить список категорий конкретного товара."""
        items = self._category_repository.list(product_id)
        return CategoryListResponseDto(
            items=[CategoryResponseDto.from_domain(c) for c in items],
            total=len(items),
        )

    def update_category(
        self,
        product_id: UUID,
        category_id: UUID,
        dto: CategoryUpdateDto,
        user_id: UUID,
    ) -> CategoryResponseDto:
        category = self._category_repository.get_by_id(product_id, category_id)
        if category is None:
            raise CategoryNotFoundException(category_id)

        name = dto.name.strip() if dto.name is not None else category.name
        if dto.name is not None and not name:
            raise EmptyCategoryNameException()

        slug = dto.slug.strip() if dto.slug is not None else category.slug
        description = (
            dto.description.strip()
            if dto.description is not None
            else category.description
        )

        updated = Category(
            id=category.id,
            name=name,
            slug=slug,
            description=description,
        )
        saved = self._category_repository.update(product_id, updated)
        if saved is None:
            raise CategoryNotFoundException(category_id)

        self._event_bus.publish(
            OperationEvent(
                user_id=user_id,
                action=OperationType.UPDATE_CATEGORY,
                target_id=category_id,
                details={"product_id": str(product_id), "name": saved.name},
            )
        )
        return CategoryResponseDto.from_domain(saved)

    def remove_category(
        self, product_id: UUID, category_id: UUID, user_id: UUID
    ) -> bool:
        if not self._category_repository.delete(product_id, category_id):
            raise CategoryNotFoundException(category_id)

        self._event_bus.publish(
            OperationEvent(
                user_id=user_id,
                action=OperationType.DELETE_CATEGORY,
                target_id=category_id,
                details={"product_id": str(product_id)},
            )
        )
        return True

    def search_categories(
        self,
        query: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> CategoryListResponseDto:
        """Поиск глобальных категорий (только v2)."""
        categories = self._category_repository.search(
            query=query,
            offset=offset,
            limit=limit,
        )
        return CategoryListResponseDto(
            items=[CategoryResponseDto.from_domain(c) for c in categories],
            total=len(categories),
        )
