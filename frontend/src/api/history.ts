import { api } from "./client";
import type {
  OrderHistoryResponse,
  ProductHistoryResponse,
  UserHistoryResponse,
} from "./types";

export type HistoryQueryParams = {
  limit?: number;
  last_event_id?: string | null;
};

function buildQuery(params?: HistoryQueryParams): string {
  const search = new URLSearchParams();
  if (params?.limit) {
    search.set("limit", String(params.limit));
  }
  if (params?.last_event_id) {
    search.set("last_event_id", params.last_event_id);
  }
  search.set("_t", String(Date.now()));
  const queryStr = search.toString();
  return queryStr ? `?${queryStr}` : "";
}

export function getMyHistory(
  params?: HistoryQueryParams,
): Promise<UserHistoryResponse> {
  return api<UserHistoryResponse>(`/api/users/me/history${buildQuery(params)}`, {
    cache: "no-store",
    headers: { "Cache-Control": "no-cache" },
  });
}

export function getUserHistory(
  userId: string,
  params?: HistoryQueryParams,
): Promise<UserHistoryResponse> {
  return api<UserHistoryResponse>(
    `/api/users/${userId}/history${buildQuery(params)}`,
    {
      cache: "no-store",
      headers: { "Cache-Control": "no-cache" },
    },
  );
}

export function getProductHistory(
  productId: string,
  params?: HistoryQueryParams,
): Promise<ProductHistoryResponse> {
  return api<ProductHistoryResponse>(
    `/api/products/${productId}/history${buildQuery(params)}`,
    {
      cache: "no-store",
      headers: { "Cache-Control": "no-cache" },
    },
  );
}

export function getOrderHistory(
  orderId: string,
  params?: HistoryQueryParams,
): Promise<OrderHistoryResponse> {
  return api<OrderHistoryResponse>(
    `/api/orders/${orderId}/history${buildQuery(params)}`,
    {
      cache: "no-store",
      headers: { "Cache-Control": "no-cache" },
    },
  );
}
