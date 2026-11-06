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
  CHANGE_PASSWORD: "Смена пароля",
  PASSWORD_RESET: "Сброс пароля",
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

export function formatDateTime(
  isoString: string,
  includeSeconds: boolean = false,
): string {
  if (!isoString) return "";
  try {
    // If the datetime string lacks a timezone indicator, treat as UTC
    const normalized =
      isoString.includes("T") &&
      !isoString.endsWith("Z") &&
      !/[+-]\d{2}(:\d{2})?$/.test(isoString)
        ? `${isoString}Z`
        : isoString;
    const d = new Date(normalized);
    if (isNaN(d.getTime())) return isoString;
    return formatRuDateTime(d, includeSeconds);
  } catch {
    return isoString;
  }
}

export function formatRuDateTime(d: Date, includeSeconds: boolean = false): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  const day = pad(d.getDate());
  const month = pad(d.getMonth() + 1);
  const year = d.getFullYear();
  const hours = pad(d.getHours());
  const minutes = pad(d.getMinutes());
  if (includeSeconds) {
    const seconds = pad(d.getSeconds());
    return `${day}.${month}.${year} ${hours}:${minutes}:${seconds}`;
  }
  return `${day}.${month}.${year} ${hours}:${minutes}`;
}

export function formatRuDateOnly(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}`;
}

export function parseRuDateTime(str: string): Date | null {
  if (!str) return null;
  const m = str.trim().match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?$/);
  if (!m) return null;
  const day = parseInt(m[1], 10);
  const month = parseInt(m[2], 10);
  const year = parseInt(m[3], 10);
  const hour = m[4] !== undefined ? parseInt(m[4], 10) : 0;
  const minute = m[5] !== undefined ? parseInt(m[5], 10) : 0;
  const second = m[6] !== undefined ? parseInt(m[6], 10) : 0;

  if (month < 1 || month > 12) return null;
  if (hour < 0 || hour > 23) return null;
  if (minute < 0 || minute > 59) return null;
  if (second < 0 || second > 59) return null;

  const daysInMonth = new Date(year, month, 0).getDate();
  if (day < 1 || day > daysInMonth) return null;

  return new Date(year, month - 1, day, hour, minute, second);
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
