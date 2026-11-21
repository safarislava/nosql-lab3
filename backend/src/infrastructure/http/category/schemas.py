from uuid import UUID

from pydantic import BaseModel, Field


class CategorySearchRequest(BaseModel):
    query: str | None = Field(
        default=None, description="Поисковый запрос по названию категории"
    )
    offset: int = Field(default=0, ge=0, description="Смещение (offset)")
    limit: int = Field(default=50, ge=1, le=100, description="Лимит на страницу")


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str
