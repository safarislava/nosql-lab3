import { FormEvent, useState } from "react";
import { getEventsByType } from "../api/history";
import type { OperationType } from "../api/types";
import { DateTimeInput } from "../components/DateTimeInput";
import { HistoryFeed } from "../components/HistoryFeed";
import {
  formatRuDateTime,
  OPERATION_TYPE_LABEL,
  parseRuDateTime,
} from "../lib/format";

const ALL_OPERATION_TYPES: OperationType[] = [
  "CREATE_PRODUCT",
  "UPDATE_PRODUCT",
  "DELETE_PRODUCT",
  "RESERVE_STOCK",
  "RESTORE_STOCK",
  "CREATE_ORDER",
  "CANCEL_ORDER",
  "APPROVE_ORDER",
  "REJECT_ORDER",
  "CHECKOUT",
  "USER_REGISTER",
  "UPDATE_PROFILE",
  "CHANGE_PASSWORD",
  "PASSWORD_RESET",
  "ADD_FAVOURITE",
  "REMOVE_FAVOURITE",
  "CLEAR_FAVOURITES",
  "ADD_CART_ITEM",
  "REMOVE_CART_ITEM",
  "UPDATE_CART_ITEM",
  "CLEAR_CART",
  "ADD_STUDENT",
  "REMOVE_STUDENT",
  "USER_LOGIN",
  "LOGIN_FAILED",
  "USER_LOGOUT",
  "USER_LOGOUT_ALL",
  "REQUEST_PASSWORD_RESET",
  "DELETE_ACCOUNT",
  "CREATE_CATEGORY",
  "UPDATE_CATEGORY",
  "DELETE_CATEGORY",
  "ASSIGN_PRODUCT_CATEGORY",
  "REMOVE_PRODUCT_CATEGORY",
  "UPLOAD_ATTACHMENT",
  "UPDATE_ATTACHMENT",
  "DELETE_ATTACHMENT",
  "ADMIN_DELETE_USER",
  "CHANGE_USER_ROLE",
  "TEACHER_ADD_STUDENT_CART",
  "TEACHER_CREATE_STUDENT_ORDER",
  "COMPLETE_ORDER",
  "PAY_ORDER",
];

export function AdminAuditPage() {
  const [selectedType, setSelectedType] = useState<OperationType>("CREATE_PRODUCT");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [limit, setLimit] = useState(50);

  // Active query applied on submit
  const [activeQuery, setActiveQuery] = useState({
    eventType: "CREATE_PRODUCT" as OperationType,
    startTime: "",
    endTime: "",
    limit: 50,
    timestamp: Date.now(),
  });

  function onApply(e: FormEvent) {
    e.preventDefault();
    setActiveQuery({
      eventType: selectedType,
      startTime,
      endTime,
      limit,
      timestamp: Date.now(),
    });
  }

  function toIso(ruDateTimeStr: string): string | undefined {
    if (!ruDateTimeStr) return undefined;
    const d = parseRuDateTime(ruDateTimeStr);
    return d ? d.toISOString() : undefined;
  }

  function setPreset(hours: number | null) {
    if (hours === null) {
      setStartTime("");
      setEndTime("");
      return;
    }
    const end = new Date();
    const start = new Date(end.getTime() - hours * 3600_000);
    setStartTime(formatRuDateTime(start));
    setEndTime(formatRuDateTime(end));
  }

  function setPresetToday() {
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    const end = new Date();
    setStartTime(formatRuDateTime(start));
    setEndTime(formatRuDateTime(end));
  }

  const parsedStart = parseRuDateTime(startTime);
  const parsedEnd = parseRuDateTime(endTime);
  const isInvalidRange = Boolean(
    parsedStart && parsedEnd && parsedStart > parsedEnd,
  );

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Аудит событий</h1>
          <p className="muted">
            Выборка событий заданного типа за период времени (хранилище Apache Cassandra)
          </p>
        </div>
      </div>

      <div className="card" style={{ padding: "16px", marginBottom: 20 }}>
        <form className="filters" onSubmit={onApply} style={{ padding: 0, margin: 0 }}>
          <label className="field">
            <span>Тип события</span>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as OperationType)}
            >
              {ALL_OPERATION_TYPES.map((type) => (
                <option key={type} value={type}>
                  {OPERATION_TYPE_LABEL[type] || type}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Дата и время от</span>
            <DateTimeInput
              value={startTime}
              onChange={setStartTime}
              placeholder="05.11.2026 00:00"
            />
          </label>

          <label className="field">
            <span>Дата и время до</span>
            <DateTimeInput
              value={endTime}
              onChange={setEndTime}
              placeholder="05.11.2026 23:59"
            />
          </label>

          <label className="field">
            <span>Лимит на страницу</span>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            >
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>

          <button className="btn btn--primary" type="submit" disabled={isInvalidRange}>
            Показать
          </button>
        </form>

        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center", marginTop: "12px", paddingTop: "12px", borderTop: "1px solid var(--border, #e2e8f0)" }}>
          <span className="muted" style={{ fontSize: "12px" }}>Быстрый выбор периода:</span>
          <button type="button" className="btn btn--ghost btn--sm" onClick={() => setPreset(1)}>
            Последний час
          </button>
          <button type="button" className="btn btn--ghost btn--sm" onClick={setPresetToday}>
            Сегодня
          </button>
          <button type="button" className="btn btn--ghost btn--sm" onClick={() => setPreset(24)}>
            24 часа
          </button>
          <button type="button" className="btn btn--ghost btn--sm" onClick={() => setPreset(24 * 7)}>
            7 дней
          </button>
          <button type="button" className="btn btn--ghost btn--sm" onClick={() => setPreset(null)}>
            Сбросить даты
          </button>
        </div>

        {isInvalidRange ? (
          <p className="error" style={{ margin: "8px 0 0", fontSize: "13px" }}>
            Дата «от» не может быть позже даты «до»
          </p>
        ) : null}
      </div>

      <div style={{ marginTop: 12 }}>
        <HistoryFeed
          key={`${activeQuery.eventType}-${activeQuery.startTime}-${activeQuery.endTime}-${activeQuery.limit}-${activeQuery.timestamp}`}
          fetchPage={(cursor) =>
            getEventsByType({
              event_type: activeQuery.eventType,
              start_time: toIso(activeQuery.startTime),
              end_time: toIso(activeQuery.endTime),
              limit: activeQuery.limit,
              last_event_id: cursor,
            })
          }
          emptyText={`Событий типа «${OPERATION_TYPE_LABEL[activeQuery.eventType] || activeQuery.eventType}» за выбранный период не найдено`}
          showUserId={true}
        />
      </div>
    </>
  );
}
