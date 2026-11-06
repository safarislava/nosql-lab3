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
  USER_LOGIN: "Вход в систему",
  LOGIN_FAILED: "Неудачный вход",
  USER_LOGOUT: "Выход из системы",
  USER_LOGOUT_ALL: "Выход со всех устройств",
  REQUEST_PASSWORD_RESET: "Запрос сброса пароля",
  DELETE_ACCOUNT: "Удаление аккаунта",
  CREATE_CATEGORY: "Создание категории",
  UPDATE_CATEGORY: "Обновление категории",
  DELETE_CATEGORY: "Удаление категории",
  ASSIGN_PRODUCT_CATEGORY: "Привязка категории",
  REMOVE_PRODUCT_CATEGORY: "Отвязка категории",
  UPLOAD_ATTACHMENT: "Загрузка вложения",
  UPDATE_ATTACHMENT: "Обновление вложения",
  DELETE_ATTACHMENT: "Удаление вложения",
  ADMIN_DELETE_USER: "Удаление пользователя (админ)",
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

export type OperationTone = "success" | "danger" | "info" | "warning" | "neutral";

export function getOperationTone(action: OperationType): OperationTone {
  switch (action) {
    case "CREATE_PRODUCT":
    case "CREATE_ORDER":
    case "APPROVE_ORDER":
    case "CHECKOUT":
    case "USER_REGISTER":
    case "CREATE_CATEGORY":
    case "UPLOAD_ATTACHMENT":
    case "ADD_STUDENT":
      return "success";

    case "DELETE_PRODUCT":
    case "CANCEL_ORDER":
    case "REJECT_ORDER":
    case "REMOVE_FAVOURITE":
    case "CLEAR_FAVOURITES":
    case "REMOVE_CART_ITEM":
    case "CLEAR_CART":
    case "REMOVE_STUDENT":
    case "LOGIN_FAILED":
    case "DELETE_ACCOUNT":
    case "DELETE_CATEGORY":
    case "DELETE_ATTACHMENT":
    case "ADMIN_DELETE_USER":
    case "REMOVE_PRODUCT_CATEGORY":
      return "danger";

    case "UPDATE_PRODUCT":
    case "RESTORE_STOCK":
    case "UPDATE_PROFILE":
    case "CHANGE_PASSWORD":
    case "PASSWORD_RESET":
    case "UPDATE_CATEGORY":
    case "UPDATE_ATTACHMENT":
    case "ASSIGN_PRODUCT_CATEGORY":
      return "info";

    case "RESERVE_STOCK":
    case "ADD_CART_ITEM":
    case "UPDATE_CART_ITEM":
    case "ADD_FAVOURITE":
    case "REQUEST_PASSWORD_RESET":
      return "warning";

    case "USER_LOGIN":
    case "USER_LOGOUT":
    case "USER_LOGOUT_ALL":
    default:
      return "neutral";
  }
}

export function getOperationEntity(action: OperationType): string {
  if (action.includes("PRODUCT")) return "Товар";
  if (action.includes("ORDER") || action === "CHECKOUT") return "Заказ";
  if (action.includes("CART")) return "Корзина";
  if (action.includes("FAVOURITE")) return "Избранное";
  if (action.includes("CATEGORY")) return "Категория";
  if (action.includes("ATTACHMENT")) return "Вложение";
  if (action.includes("LOGIN") || action.includes("LOGOUT")) return "Сессия";
  if (action.includes("PASSWORD")) return "Безопасность";
  if (action.includes("STUDENT")) return "Студенты";
  if (
    action.includes("USER") ||
    action.includes("ACCOUNT") ||
    action.includes("PROFILE")
  ) {
    return "Пользователь";
  }
  return "Операция";
}

export const OPERATION_USER_LABEL: Record<OperationType, string> = {
  CREATE_PRODUCT: "Товар создан",
  UPDATE_PRODUCT: "Товар обновлен",
  DELETE_PRODUCT: "Товар удален",
  RESERVE_STOCK: "Резервирование на складе",
  RESTORE_STOCK: "Пополнение склада",
  CREATE_ORDER: "Заказ оформлен",
  CANCEL_ORDER: "Заказ отменен",
  APPROVE_ORDER: "Заказ подтвержден",
  REJECT_ORDER: "Заказ отклонен",
  CHECKOUT: "Корзина оформлена в заказ",
  USER_REGISTER: "Регистрация аккаунта",
  UPDATE_PROFILE: "Профиль обновлен",
  CHANGE_PASSWORD: "Пароль изменен",
  PASSWORD_RESET: "Пароль сброшен",
  ADD_FAVOURITE: "Добавлено в избранное",
  REMOVE_FAVOURITE: "Удалено из избранного",
  CLEAR_FAVOURITES: "Избранное очищено",
  ADD_CART_ITEM: "Товар добавлен в корзину",
  REMOVE_CART_ITEM: "Товар удален из корзины",
  UPDATE_CART_ITEM: "Количество в корзине изменено",
  CLEAR_CART: "Корзина очищена",
  ADD_STUDENT: "Студент прикреплен",
  REMOVE_STUDENT: "Студент откреплен",
  USER_LOGIN: "Вход в аккаунт",
  LOGIN_FAILED: "Ошибка входа в аккаунт",
  USER_LOGOUT: "Выход из аккаунта",
  USER_LOGOUT_ALL: "Выход со всех устройств",
  REQUEST_PASSWORD_RESET: "Запрос восстановления пароля",
  DELETE_ACCOUNT: "Аккаунт удален",
  CREATE_CATEGORY: "Категория добавлена",
  UPDATE_CATEGORY: "Категория обновлена",
  DELETE_CATEGORY: "Категория удалена",
  ASSIGN_PRODUCT_CATEGORY: "Категория привязана к товару",
  REMOVE_PRODUCT_CATEGORY: "Категория отвязана от товара",
  UPLOAD_ATTACHMENT: "Файл прикреплен",
  UPDATE_ATTACHMENT: "Файл обновлен",
  DELETE_ATTACHMENT: "Файл удален",
  ADMIN_DELETE_USER: "Пользователь удален администратором",
};

export const DETAIL_KEY_LABELS: Record<string, string> = {
  name: "Название",
  price: "Цена",
  quantity: "Количество",
  amount: "Количество",
  remaining_quantity: "Остаток на складе",
  restored_quantity: "Возвращено на склад",
  total_amount: "Сумма",
  orders_count: "Заказов",
  items_count: "Позиций",
  email: "Email",
  role: "Роль",
  filename: "Файл",
  size_bytes: "Размер файла",
  description: "Описание",
  slug: "Слаг",
  reason: "Причина",
  ip_address: "IP адрес",
  product_id: "ID товара",
  category_id: "ID категории",
  student_id: "ID студента",
  target_user_id: "ID пользователя",
};

const TECHNICAL_KEYS = new Set([
  "product_id",
  "category_id",
  "student_id",
  "target_user_id",
  "ip_address",
]);

export function isTechnicalDetailKey(key: string): boolean {
  return TECHNICAL_KEYS.has(key);
}

export function formatDetailValue(key: string, value: unknown): string {
  if (value === null || value === undefined) return "";
  if (key === "price" || key === "total_amount") {
    return formatPrice(String(value));
  }
  if (key === "size_bytes" && typeof value === "number") {
    return formatBytes(value);
  }
  if (key === "role" && typeof value === "string") {
    return roleLabel(value as UserRole);
  }
  if (
    key === "quantity" ||
    key === "amount" ||
    key === "remaining_quantity" ||
    key === "restored_quantity"
  ) {
    return `${value} шт.`;
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}
