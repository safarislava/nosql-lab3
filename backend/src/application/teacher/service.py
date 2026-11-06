import logging
from uuid import UUID

from application.event_bus import IEventBus
from application.favourites.dto import AddFavouriteDto
from application.favourites.service import FavouritesService
from application.product.service import ProductService
from application.user.dto import UserResponseDto
from application.user.service import UserService
from domain.history import OperationEvent, OperationType
from domain.teacher import Teacher
from domain.user import UserRole

from .dto import (
    AddProductToStudentsDto,
    BatchAddProductResultDto,
    TeacherResponseDto,
)
from .exceptions import (
    CannotAddSelfAsStudentException,
    InvalidStudentRoleException,
    StudentAlreadyAssignedException,
    StudentNotAssignedException,
    TeacherNotFoundException,
)
from .repository import ITeacherRepository

logger = logging.getLogger(__name__)


class TeacherService:
    def __init__(
        self,
        teacher_repository: ITeacherRepository,
        user_service: UserService,
        product_service: ProductService,
        favourites_service: FavouritesService,
        event_bus: IEventBus,
    ):
        self._teacher_repository = teacher_repository
        self._user_service = user_service
        self._product_service = product_service
        self._favourites_service = favourites_service
        self._event_bus = event_bus

    def _build_teacher_dto(self, teacher: Teacher) -> TeacherResponseDto:
        students = self._teacher_repository.get_students(teacher.id)
        students_dto = [UserResponseDto.from_domain(s) for s in students]
        return TeacherResponseDto.from_domain(teacher, students=students_dto)

    def get_teacher(self, teacher_id: UUID) -> TeacherResponseDto:
        teacher = self._get_teacher(teacher_id)
        return self._build_teacher_dto(teacher)

    def get_students(self, teacher_id: UUID) -> list[UserResponseDto]:
        if not self._teacher_repository.exists_by_id(teacher_id):
            raise TeacherNotFoundException(teacher_id)
        students = self._teacher_repository.get_students(teacher_id)
        return [UserResponseDto.from_domain(s) for s in students]

    def add_student(self, teacher_id: UUID, student_id: UUID) -> TeacherResponseDto:
        if teacher_id == student_id:
            raise CannotAddSelfAsStudentException()

        student = self._user_service.get_by_id(student_id)
        if student.role != UserRole.STUDENT:
            raise InvalidStudentRoleException(student_id)

        teacher = self._get_teacher(teacher_id)
        if teacher.has_student(student_id):
            raise StudentAlreadyAssignedException(student_id)

        self._teacher_repository.assign_student(teacher_id, student_id)

        self._event_bus.publish(
            OperationEvent(
                user_id=teacher_id,
                action=OperationType.ADD_STUDENT,
                target_id=student_id,
            )
        )

        teacher = self._get_teacher(teacher_id)
        return self._build_teacher_dto(teacher)

    def remove_student(self, teacher_id: UUID, student_id: UUID) -> TeacherResponseDto:
        if not self._teacher_repository.unassign_student(teacher_id, student_id):
            if not self._teacher_repository.exists_by_id(teacher_id):
                raise TeacherNotFoundException(teacher_id)
            raise StudentNotAssignedException(student_id)

        self._event_bus.publish(
            OperationEvent(
                user_id=teacher_id,
                action=OperationType.REMOVE_STUDENT,
                target_id=student_id,
            )
        )

        teacher = self._get_teacher(teacher_id)
        return self._build_teacher_dto(teacher)

    def add_product_to_all_students(
        self,
        teacher_id: UUID,
        dto: AddProductToStudentsDto,
    ) -> BatchAddProductResultDto:
        self._product_service.ensure_exists(dto.product_id)

        teacher = self._get_teacher(teacher_id)
        student_ids = teacher.get_student_ids()

        fav_dto = AddFavouriteDto(product_id=dto.product_id)
        for student_id in student_ids:
            self._favourites_service.add_product(
                user_id=student_id,
                dto=fav_dto,
                added_by_user_id=teacher_id,
                check_product_exists=False,
            )

        return BatchAddProductResultDto(
            product_id=dto.product_id,
            affected_students=len(student_ids),
            student_ids=student_ids,
        )

    def _get_teacher(self, teacher_id: UUID) -> Teacher:
        teacher = self._teacher_repository.get_by_id(teacher_id)
        if teacher is None:
            raise TeacherNotFoundException(teacher_id)
        return teacher
