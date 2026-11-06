import { useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";
import type { OperationEvent } from "../api/types";
import {
  formatDateTime,
  formatEventDetails,
  OPERATION_TYPE_LABEL,
} from "../lib/format";

type HistoryFeedProps = {
  fetchPage: (
    cursor?: string | null,
  ) => Promise<{ events: OperationEvent[]; next_cursor?: string | null }>;
  emptyText?: string;
  showUserId?: boolean;
};

export function HistoryFeed({
  fetchPage,
  emptyText = "Событий пока нет",
  showUserId = true,
}: HistoryFeedProps) {
  const [events, setEvents] = useState<OperationEvent[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");

  const fetchRef = useRef(fetchPage);
  fetchRef.current = fetchPage;

  async function loadMore() {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    setError("");
    try {
      const res = await fetchRef.current(nextCursor);
      setEvents((prev) => [...prev, ...(res.events || [])]);
      setNextCursor(res.next_cursor ?? null);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось загрузить следующие события",
      );
    } finally {
      setLoadingMore(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    fetchRef.current(null)
      .then((res) => {
        if (cancelled) return;
        setEvents(res.events || []);
        setNextCursor(res.next_cursor ?? null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "Не удалось загрузить историю событий",
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="history-feed">
      {error ? <p className="error">{error}</p> : null}
      {loading ? (
        <div className="skeleton" style={{ height: 120, margin: "12px 0" }} />
      ) : events.length === 0 ? (
        <div className="card empty" style={{ padding: "20px" }}>
          {emptyText}
        </div>
      ) : (
        <div className="history-list">
          {events.map((event) => {
            const detailsText = formatEventDetails(event);
            return (
              <div key={event.id} className="card history-item">
                <div className="history-item__head">
                  <span className="history-badge">
                    {OPERATION_TYPE_LABEL[event.action] || event.action}
                  </span>
                  <span
                    className="history-time muted"
                    title={formatDateTime(event.timestamp, true)}
                  >
                    {formatDateTime(event.timestamp)}
                  </span>
                </div>
                <div className="history-item__meta muted">
                  {showUserId ? <span>Пользователь: {event.user_id}</span> : null}
                  {event.target_id ? <span>Цель: {event.target_id}</span> : null}
                  <span className="history-id" title={event.id}>
                    ID: {event.id.slice(0, 8)}...
                  </span>
                </div>
                {detailsText ? (
                  <div className="history-item__details">
                    <span className="muted">Детали: </span>
                    <code>{detailsText}</code>
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      )}

      {nextCursor ? (
        <div className="history-load-more">
          <button
            type="button"
            className="btn btn--ghost"
            disabled={loadingMore}
            onClick={() => void loadMore()}
          >
            {loadingMore ? "Загрузка..." : "Загрузить ещё"}
          </button>
        </div>
      ) : null}
    </div>
  );
}
