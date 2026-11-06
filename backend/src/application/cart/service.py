from decimal import Decimal
from uuid import UUID

from application.event_bus import IEventBus
from application.product.service import ProductService
from domain.cart import Cart
from domain.history import OperationEvent, OperationType

from .dto import (
    CartItemResponseDto,
    CartResponseDto,
    UpdateCartProductDto,
)
from .exceptions import (
    CartProductNotFoundException,
)
from .repository import ICartRepository


class CartService:
    def __init__(
        self,
        cart_repository: ICartRepository,
        product_service: ProductService,
        event_bus: IEventBus,
    ) -> None:
        self._cart_repository = cart_repository
        self._product_service = product_service
        self._event_bus = event_bus

    def _build_response_dto(self, cart: Cart) -> CartResponseDto:
        if not cart.cart_products:
            return CartResponseDto(
                user_id=cart.user_id,
                items=[],
                total_items=0,
                total_amount=Decimal("0.00"),
                has_unavailable_items=False,
            )

        product_ids = [p.product_id for p in cart.cart_products]
        products_map = self._product_service.get_by_ids(product_ids)

        items: list[CartItemResponseDto] = []
        total_amount = Decimal("0.00")
        has_unavailable = False

        for item in cart.cart_products:
            prod_dto = products_map.get(item.product_id)
            if prod_dto is not None:
                is_available = prod_dto.quantity >= item.quantity
                if not is_available:
                    has_unavailable = True
                subtotal = prod_dto.price * item.quantity
                if is_available:
                    total_amount += subtotal
                items.append(
                    CartItemResponseDto(
                        product_id=item.product_id,
                        quantity=item.quantity,
                        updated_at=item.updated_at,
                        product=prod_dto,
                        subtotal=subtotal,
                        is_available=is_available,
                        available_stock=prod_dto.quantity,
                    )
                )
            else:
                has_unavailable = True
                items.append(
                    CartItemResponseDto(
                        product_id=item.product_id,
                        quantity=item.quantity,
                        updated_at=item.updated_at,
                        product=None,
                        subtotal=Decimal("0.00"),
                        is_available=False,
                        available_stock=0,
                    )
                )

        return CartResponseDto(
            user_id=cart.user_id,
            items=items,
            total_items=cart.get_total_items(),
            total_amount=total_amount,
            has_unavailable_items=has_unavailable,
        )

    def get_by_user_id(self, user_id: UUID) -> CartResponseDto:
        cart = self._get_or_create(user_id)
        return self._build_response_dto(cart)

    def is_in_cart(self, user_id: UUID, product_id: UUID) -> bool:
        cart = self._cart_repository.get_by_user_id(user_id)
        if cart is None:
            return False
        return cart.has_product(product_id)

    def update_quantity(
        self,
        user_id: UUID,
        dto: UpdateCartProductDto,
    ) -> CartResponseDto:
        cart = self._get_or_create(user_id)
        is_new_item = not cart.has_product(dto.product_id)

        if dto.quantity <= 0:
            cart = self._cart_repository.remove_item_and_get(user_id, dto.product_id)
            action = OperationType.REMOVE_CART_ITEM
        else:
            self._product_service.ensure_exists(dto.product_id)
            cart = self._cart_repository.set_item_quantity_and_get(
                user_id=user_id,
                product_id=dto.product_id,
                quantity=dto.quantity,
            )
            action = (
                OperationType.ADD_CART_ITEM
                if is_new_item
                else OperationType.UPDATE_CART_ITEM
            )

        self._event_bus.publish(
            OperationEvent(
                user_id=user_id,
                action=action,
                target_id=dto.product_id,
                details={"new_quantity": dto.quantity},
            )
        )

        return self._build_response_dto(cart)

    def remove_product(
        self,
        user_id: UUID,
        product_id: UUID,
    ) -> CartResponseDto:
        cart = self._get_or_create(user_id)
        if not cart.has_product(product_id):
            raise CartProductNotFoundException(product_id)

        updated_cart = self._cart_repository.remove_item_and_get(user_id, product_id)

        self._event_bus.publish(
            OperationEvent(
                user_id=user_id,
                action=OperationType.REMOVE_CART_ITEM,
                target_id=product_id,
            )
        )

        return self._build_response_dto(updated_cart)

    def clear(self, user_id: UUID) -> CartResponseDto:
        self._cart_repository.delete_by_user_id(user_id)

        self._event_bus.publish(
            OperationEvent(
                user_id=user_id,
                action=OperationType.CLEAR_CART,
            )
        )

        return self._build_response_dto(Cart(user_id=user_id))

    def _get_or_create(self, user_id: UUID) -> Cart:
        cart = self._cart_repository.get_by_user_id(user_id)
        if cart is None:
            cart = Cart(user_id=user_id)
        return cart
