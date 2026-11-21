import { api } from "./client";
import type { Order, OrderList, OrderStatus } from "./types";

export function listMyOrders(status?: OrderStatus): Promise<OrderList> {
  return api<OrderList>("/api/users/me/orders/search", {
    method: "POST",
    body: JSON.stringify({
      status: status || null,
      offset: 0,
      limit: 50,
    }),
    cache: "no-store",
    headers: { "Cache-Control": "no-cache" },
  });
}

export function cancelOrder(orderId: string): Promise<Order> {
  return api<Order>(`/api/users/me/orders/${orderId}/cancel`, {
    method: "POST",
  });
}

export function listAllOrders(status?: OrderStatus): Promise<OrderList> {
  return api<OrderList>("/api/orders/search", {
    method: "POST",
    body: JSON.stringify({
      status: status || null,
      offset: 0,
      limit: 50,
    }),
    cache: "no-store",
    headers: { "Cache-Control": "no-cache" },
  });
}

export function approveOrder(orderId: string): Promise<Order> {
  return api<Order>(`/api/orders/${orderId}/approve`, { method: "POST" });
}

export function rejectOrder(orderId: string): Promise<Order> {
  return api<Order>(`/api/orders/${orderId}/reject`, { method: "POST" });
}


