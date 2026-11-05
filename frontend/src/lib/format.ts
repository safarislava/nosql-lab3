import type { OperationEvent, OperationType, OrderStatus, UserRole } from "../api/types";

export function formatPrice(price: string | number): string {
  const num = typeof price === "string" ? parseFloat(price) : price;
  if (isNaN(num)) {
    return `${price} ₽`;
  }
  return `${num.toLocaleString("ru-RU")} ₽`;
}

export const ORDER_STATUS_LABEL: Record<OrderStatus, string> = {
  CREATED: "Создана",
  APPROVED: "Одобрена",
  REJECTED: "Отклонена",
  CANCELLED: "Отменена",
};

export const OPERATION_TYPE_LABEL: Record<OperationType, string> = {
  CREATE_PRODUCT: "Создание товара",
  UPDATE_PRODUCT: "Обновление товара",
  DELETE_PRODUCT: "Удаление товара",
  RESERVE_STOCK: "Резерв остатка",
  RESTORE_STOCK: "Возврат остатка",
  CREATE_ORDER: "Создание заказа",
  CANCEL_ORDER: "Отмена заказа",
  APPROVE_ORDER: "Подтверждение заказа",
  REJECT_ORDER: "Отклонение заказа",
  CHECKOUT: "Оформление корзины",
  USER_REGISTER: "Регистрация",
  UPDATE_PROFILE: "Обновление профиля",
  ADD_FAVOURITE: "Добавление в избранное",
  REMOVE_FAVOURITE: "Удаление из избранного",
  CLEAR_FAVOURITES: "Очистка избранного",
  ADD_CART_ITEM: "Добавление в корзину",
  REMOVE_CART_ITEM: "Удаление из корзины",
  UPDATE_CART_ITEM: "Изменение кол-ва в корзине",
  CLEAR_CART: "Очистка корзины",
  ADD_STUDENT: "Добавление студента",
  REMOVE_STUDENT: "Удаление студента",
};

export function formatDateTime(isoString: string): string {
  if (!isoString) return "";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return isoString;
  }
}

export function formatEventDetails(event: OperationEvent): string {
  if (!event.details || Object.keys(event.details).length === 0) {
    return "";
  }
  const parts: string[] = [];
  for (const [key, value] of Object.entries(event.details)) {
    if (value === null || value === undefined) continue;
    if (typeof value === "object") {
      parts.push(`${key}: ${JSON.stringify(value)}`);
    } else {
      parts.push(`${key}: ${String(value)}`);
    }
  }
  return parts.join(", ");
}


export function roleLabel(role: UserRole): string {
  switch (role) {
    case "STUDENT":
      return "Студент";
    case "TEACHER":
      return "Преподаватель";
    case "ADMIN":
      return "Администратор";
    default:
      return role;
  }
}

export function formatBytes(bytes: number): string {
  if (!bytes || bytes <= 0) return "0 Б";
  const units = ["Б", "КБ", "МБ", "ГБ"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i] || "Б"}`;
}
