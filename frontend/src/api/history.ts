import { api } from "./client";
import type {
  EventsByTypeResponse,
  OperationType,
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

export type EventsByTypeParams = HistoryQueryParams & {
  event_type: OperationType;
  start_time?: string | null;
  end_time?: string | null;
};

export function getEventsByType(
  params: EventsByTypeParams,
): Promise<EventsByTypeResponse> {
  const search = new URLSearchParams();
  search.set("event_type", params.event_type);
  if (params.start_time) search.set("start_time", params.start_time);
  if (params.end_time) search.set("end_time", params.end_time);
  if (params.limit) search.set("limit", String(params.limit));
  if (params.last_event_id) search.set("last_event_id", params.last_event_id);
  search.set("_t", String(Date.now()));
  return api<EventsByTypeResponse>(`/api/history?${search.toString()}`, {
    cache: "no-store",
    headers: { "Cache-Control": "no-cache" },
  });
}

