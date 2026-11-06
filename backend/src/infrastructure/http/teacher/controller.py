from uuid import UUID

from fastapi import APIRouter, status

from domain.user import UserRole
from infrastructure.http.auth.dependencies import require_roles
from infrastructure.http.middleware.authentication_middleware import CurrentUserDep
from infrastructure.http.user.schemas import UserResponse

from .dependencies import TeacherServiceDep
from .schemas import (
    AddProductToStudentsRequest,
    AddStudentRequest,
    BatchAddProductResponse,
    TeacherResponse,
)

router = APIRouter(tags=["Teachers"])


def _get_teacher_profile(
    teacher_id: UUID,
    service: TeacherServiceDep,
) -> TeacherResponse:
    dto = service.get_teacher(teacher_id)
    return TeacherResponse.from_dto(dto)


def _get_students(
    teacher_id: UUID,
    service: TeacherServiceDep,
) -> list[UserResponse]:
    students = service.get_students(teacher_id)
    return [UserResponse.from_dto(s) for s in students]


def _add_student(
    teacher_id: UUID,
    request: AddStudentRequest,
    service: TeacherServiceDep,
) -> TeacherResponse:
    dto = service.add_student(
        teacher_id=teacher_id,
        student_id=request.student_id,
    )
    return TeacherResponse.from_dto(dto)


def _remove_student(
    teacher_id: UUID,
    student_id: UUID,
    service: TeacherServiceDep,
) -> TeacherResponse:
    dto = service.remove_student(
        teacher_id=teacher_id,
        student_id=student_id,
    )
    return TeacherResponse.from_dto(dto)


def _add_product_to_all_students(
    teacher_id: UUID,
    request: AddProductToStudentsRequest,
    service: TeacherServiceDep,
) -> BatchAddProductResponse:
    dto = service.add_product_to_all_students(
        teacher_id=teacher_id,
        dto=request.to_dto(),
    )
    return BatchAddProductResponse.from_dto(dto)


@router.get(
    "/users/me/teacher",
    dependencies=[require_roles(UserRole.TEACHER)],
    response_model=TeacherResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить профиль текущего преподавателя со списком ID учеников",
)
def get_my_teacher_profile(
    current_user: CurrentUserDep,
    service: TeacherServiceDep,
) -> TeacherResponse:
    return _get_teacher_profile(current_user.id, service)


@router.get(
    "/users/{user_id}/teacher",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=TeacherResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить профиль преподавателя по ID (Admin)",
)
def get_teacher_profile_by_id(
    user_id: UUID,
    service: TeacherServiceDep,
) -> TeacherResponse:
    return _get_teacher_profile(user_id, service)


@router.get(
    "/users/me/teacher/students",
    dependencies=[require_roles(UserRole.TEACHER)],
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить подробный список учеников текущего преподавателя",
)
def get_my_students(
    current_user: CurrentUserDep,
    service: TeacherServiceDep,
) -> list[UserResponse]:
    return _get_students(current_user.id, service)


@router.get(
    "/users/{user_id}/teacher/students",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить подробный список учеников преподавателя по ID (Admin)",
)
def get_students_by_id(
    user_id: UUID,
    service: TeacherServiceDep,
) -> list[UserResponse]:
    return _get_students(user_id, service)


@router.post(
    "/users/me/teacher/students",
    dependencies=[require_roles(UserRole.TEACHER)],
    response_model=TeacherResponse,
    status_code=status.HTTP_200_OK,
    summary="Прикрепить ученика к текущему преподавателю",
)
def add_student_me(
    request: AddStudentRequest,
    current_user: CurrentUserDep,
    service: TeacherServiceDep,
) -> TeacherResponse:
    return _add_student(current_user.id, request, service)


@router.post(
    "/users/{user_id}/teacher/students",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=TeacherResponse,
    status_code=status.HTTP_200_OK,
    summary="Прикрепить ученика к преподавателю по ID (Admin)",
)
def add_student_by_id(
    user_id: UUID,
    request: AddStudentRequest,
    service: TeacherServiceDep,
) -> TeacherResponse:
    return _add_student(user_id, request, service)


@router.delete(
    "/users/me/teacher/students/{student_id}",
    dependencies=[require_roles(UserRole.TEACHER)],
    response_model=TeacherResponse,
    status_code=status.HTTP_200_OK,
    summary="Открепить ученика от текущего преподавателя",
)
def remove_student_me(
    student_id: UUID,
    current_user: CurrentUserDep,
    service: TeacherServiceDep,
) -> TeacherResponse:
    return _remove_student(current_user.id, student_id, service)


@router.delete(
    "/users/{user_id}/teacher/students/{student_id}",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=TeacherResponse,
    status_code=status.HTTP_200_OK,
    summary="Открепить ученика от преподавателя по ID (Admin)",
)
def remove_student_by_id(
    user_id: UUID,
    student_id: UUID,
    service: TeacherServiceDep,
) -> TeacherResponse:
    return _remove_student(user_id, student_id, service)


@router.post(
    "/users/me/teacher/students/favourites",
    dependencies=[require_roles(UserRole.TEACHER)],
    response_model=BatchAddProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Добавить товар в избранное всем своим ученикам",
)
def add_product_to_all_students_me(
    request: AddProductToStudentsRequest,
    current_user: CurrentUserDep,
    service: TeacherServiceDep,
) -> BatchAddProductResponse:
    return _add_product_to_all_students(current_user.id, request, service)


@router.post(
    "/users/{user_id}/teacher/students/favourites",
    dependencies=[require_roles(UserRole.ADMIN)],
    response_model=BatchAddProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Добавить товар в избранное всем ученикам преподавателя по ID (Admin)",
)
def add_product_to_all_students_by_id(
    user_id: UUID,
    request: AddProductToStudentsRequest,
    service: TeacherServiceDep,
) -> BatchAddProductResponse:
    return _add_product_to_all_students(user_id, request, service)
