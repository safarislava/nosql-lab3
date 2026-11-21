import { api } from "./client";
import type { Cart, CheckoutResult, Favourites, OrderList } from "./types";

export function getUserFavourites(userId: string): Promise<Favourites> {
  return api<Favourites>(`/api/users/${userId}/favourites`);
}

export function addUserFavourite(userId: string, productId: string): Promise<Favourites> {
  return api<Favourites>(`/api/users/${userId}/favourites`, {
    method: "POST",
    body: JSON.stringify({ product_id: productId }),
  });
}

export function removeUserFavourite(userId: string, productId: string): Promise<Favourites> {
  return api<Favourites>(`/api/users/${userId}/favourites/${productId}`, {
    method: "DELETE",
  });
}

export function clearUserFavourites(userId: string): Promise<Favourites> {
  return api<Favourites>(`/api/users/${userId}/favourites`, { method: "DELETE" });
}

export function getUserCart(userId: string): Promise<Cart> {
  return api<Cart>(`/api/users/${userId}/cart`);
}

export function setUserCartQuantity(
  userId: string,
  productId: string,
  quantity: number,
): Promise<Cart> {
  return api<Cart>(`/api/users/${userId}/cart/items/${productId}`, {
    method: "PATCH",
    body: JSON.stringify({ quantity }),
  });
}

export function clearUserCart(userId: string): Promise<Cart> {
  return api<Cart>(`/api/users/${userId}/cart`, { method: "DELETE" });
}

export function checkoutUser(userId: string): Promise<CheckoutResult> {
  return api<CheckoutResult>(`/api/users/${userId}/checkout`, { method: "POST" });
}

export function getUserOrders(userId: string): Promise<OrderList> {
  return api<OrderList>(`/api/users/${userId}/orders/search`, {
    method: "POST",
    body: JSON.stringify({ limit: 50, offset: 0 }),
  });
}
