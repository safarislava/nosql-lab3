import { FormEvent, useState } from "react";
import { getEventsByType } from "../api/history";
import type { OperationType } from "../api/types";
import { HistoryFeed } from "../components/HistoryFeed";
import { OPERATION_TYPE_LABEL } from "../lib/format";

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
  "ADD_FAVOURITE",
  "REMOVE_FAVOURITE",
  "CLEAR_FAVOURITES",
  "ADD_CART_ITEM",
  "REMOVE_CART_ITEM",
  "UPDATE_CART_ITEM",
  "CLEAR_CART",
  "ADD_STUDENT",
  "REMOVE_STUDENT",
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

  function toIso(localDateTimeStr: string): string | undefined {
    if (!localDateTimeStr) return undefined;
    const d = new Date(localDateTimeStr);
    return isNaN(d.getTime()) ? undefined : d.toISOString();
  }

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

      <form className="card filters" onSubmit={onApply} style={{ marginBottom: 20 }}>
        <label className="field">
          <span>Тип события</span>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value as OperationType)}
          >
            {ALL_OPERATION_TYPES.map((type) => (
              <option key={type} value={type}>
                {OPERATION_TYPE_LABEL[type] || type} ({type})
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Дата и время от</span>
          <input
            type="datetime-local"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
          />
        </label>

        <label className="field">
          <span>Дата и время до</span>
          <input
            type="datetime-local"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
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

        <button className="btn btn--primary" type="submit">
          Показать
        </button>
      </form>

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
