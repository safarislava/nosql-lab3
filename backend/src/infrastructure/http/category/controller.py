from fastapi import APIRouter, status

from application.category.exceptions import (
    CategorySearchNotSupportedInV1Exception,
)
from infrastructure.environment.settings import settings
from infrastructure.http.category.dependencies import CategoryServiceDep
from infrastructure.http.category.schemas import (
    CategoryResponse,
    CategorySearchRequest,
)

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "/search",
    response_model=list[CategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Поиск категорий",
    description=(
        "Поиск категорий по названию. Доступно только для схемы версии 2. "
        "В версии 1 возвращает 400 Bad Request."
    ),
)
def search_categories(
    service: CategoryServiceDep,
    request: CategorySearchRequest | None = None,
) -> list[CategoryResponse]:
    if settings.app_version < 2:
        raise CategorySearchNotSupportedInV1Exception()
    search_req = request or CategorySearchRequest()
    result = service.search_categories(
        query=search_req.query, offset=search_req.offset, limit=search_req.limit
    )
    return [
        CategoryResponse(
            id=c.id,
            name=c.name,
            slug=c.slug,
            description=c.description,
        )
        for c in result.items
    ]
