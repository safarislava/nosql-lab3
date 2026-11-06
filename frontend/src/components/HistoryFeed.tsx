import { useEffect, useMemo, useRef, useState } from "react";
import { ApiError } from "../api/client";
import type { OperationEvent } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import {
  DETAIL_KEY_LABELS,
  formatDateTime,
  formatDetailValue,
  getOperationEntity,
  getOperationTone,
  isTechnicalDetailKey,
  OPERATION_TYPE_LABEL,
  OPERATION_USER_LABEL,
} from "../lib/format";

type HistoryFeedProps = {
  fetchPage: (
    cursor?: string | null,
  ) => Promise<{ events: OperationEvent[]; next_cursor?: string | null }>;
  emptyText?: string;
  showUserId?: boolean;
  mode?: "auto" | "admin" | "user";
};

export function HistoryFeed({
  fetchPage,
  emptyText = "Событий пока нет",
  showUserId = true,
  mode = "auto",
}: HistoryFeedProps) {
  const { user } = useAuth();
  const isAdminView =
    mode === "admin" || (mode !== "user" && user?.role === "ADMIN");

  const [events, setEvents] = useState<OperationEvent[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");

  // Admin interactive states
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [expandedJsonMap, setExpandedJsonMap] = useState<Record<string, boolean>>({});
  const [searchFilter, setSearchFilter] = useState("");

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

  function handleCopy(text: string, key: string) {
    if (!navigator.clipboard) return;
    navigator.clipboard.writeText(text).then(() => {
      setCopiedKey(key);
      setTimeout(() => {
        setCopiedKey((curr) => (curr === key ? null : curr));
      }, 1600);
    });
  }

  function toggleJson(eventId: string) {
    setExpandedJsonMap((prev) => ({
      ...prev,
      [eventId]: !prev[eventId],
    }));
  }

  // Filter events locally by search in admin view
  const filteredEvents = useMemo(() => {
    if (!isAdminView || !searchFilter.trim()) return events;
    const q = searchFilter.toLowerCase().trim();
    return events.filter((ev) => {
      if (ev.id.toLowerCase().includes(q)) return true;
      if (ev.user_id.toLowerCase().includes(q)) return true;
      if (ev.target_id && ev.target_id.toLowerCase().includes(q)) return true;
      if (ev.action.toLowerCase().includes(q)) return true;
      const label = OPERATION_TYPE_LABEL[ev.action];
      if (label && label.toLowerCase().includes(q)) return true;
      if (ev.details) {
        const detailsStr = JSON.stringify(ev.details).toLowerCase();
        if (detailsStr.includes(q)) return true;
      }
      return false;
    });
  }, [events, isAdminView, searchFilter]);

  return (
    <div className="history-feed">
      {error ? <p className="error">{error}</p> : null}

      {/* Admin Quick Search & Counter */}
      {isAdminView && events.length > 0 ? (
        <div className="history-admin-toolbar">
          <div className="history-search-wrap">
            <svg
              className="history-search-icon"
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="search"
              className="history-search-input"
              placeholder="Быстрый поиск по карточкам (по действию, ID, email, деталям)..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
            />
            {searchFilter ? (
              <button
                type="button"
                className="history-search-clear"
                onClick={() => setSearchFilter("")}
                title="Очистить поиск"
              >
                ✕
              </button>
            ) : null}
          </div>
          <span className="history-count muted">
            Загружено: <strong>{filteredEvents.length}</strong>
            {events.length !== filteredEvents.length ? ` из ${events.length}` : ""}
          </span>
        </div>
      ) : null}

      {loading ? (
        <div className="skeleton" style={{ height: 140, margin: "12px 0" }} />
      ) : events.length === 0 ? (
        <div className="card empty" style={{ padding: "28px", textAlign: "center" }}>
          {emptyText}
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="card empty" style={{ padding: "20px", textAlign: "center" }}>
          По запросу «{searchFilter}» среди загруженных событий ничего не найдено
        </div>
      ) : (
        <div className="history-list">
          {filteredEvents.map((event) => {
            const tone = getOperationTone(event.action);
            const entity = getOperationEntity(event.action);
            const hasDetails =
              event.details && Object.keys(event.details).length > 0;
            const isJsonExpanded = Boolean(expandedJsonMap[event.id]);

            // For regular users: filter out raw technical IDs
            const userFriendlyDetails = hasDetails
              ? Object.entries(event.details || {}).filter(
                  ([k, v]) =>
                    v !== null &&
                    v !== undefined &&
                    v !== "" &&
                    !isTechnicalDetailKey(k),
                )
              : [];

            // For admin users: all details
            const adminDetails = hasDetails
              ? Object.entries(event.details || {}).filter(
                  ([, v]) => v !== null && v !== undefined && v !== "",
                )
              : [];

            if (!isAdminView) {
              /* ============================================================ */
              /*           ОПРЯТНЫЙ ВИД ДЛЯ ОБЫЧНОГО ПОЛЬЗОВАТЕЛЯ             */
              /* ============================================================ */
              return (
                <div
                  key={event.id}
                  className={`card history-user-card history-card--tone-${tone}`}
                >
                  <div className="history-user-card__main">
                    <div className="history-user-card__header">
                      <span className={`history-user-badge history-badge--${tone}`}>
                        {OPERATION_USER_LABEL[event.action] ||
                          OPERATION_TYPE_LABEL[event.action] ||
                          event.action}
                      </span>
                      <time
                        className="history-time muted"
                        dateTime={event.timestamp}
                        title={formatDateTime(event.timestamp, true)}
                      >
                        {formatDateTime(event.timestamp)}
                      </time>
                    </div>

                    {userFriendlyDetails.length > 0 ? (
                      <div className="history-user-details">
                        {userFriendlyDetails.map(([key, value]) => {
                          const label = DETAIL_KEY_LABELS[key] || key;
                          const formattedVal = formatDetailValue(key, value);
                          return (
                            <span key={key} className="history-chip history-chip--clean">
                              <span className="history-chip__key">{label}:</span>
                              <span className="history-chip__val">{formattedVal}</span>
                            </span>
                          );
                        })}
                      </div>
                    ) : null}
                  </div>
                </div>
              );
            }

            /* ============================================================ */
            /*           РАСШИРЕННЫЙ СЛУЖЕБНЫЙ ВИД ДЛЯ АДМИНИСТРАТОРА        */
            /* ============================================================ */
            const userCopyKey = `user-${event.id}`;
            const targetCopyKey = `target-${event.id}`;
            const eventCopyKey = `event-${event.id}`;
            const jsonCopyKey = `json-${event.id}`;

            return (
              <div
                key={event.id}
                className={`card history-admin-card history-card--tone-${tone}`}
              >
                {/* 1. Верхняя панель: Сущность + Действие + Время */}
                <div className="history-admin-card__head">
                  <div className="history-admin-card__title-group">
                    <span className="history-entity-tag">{entity}</span>
                    <span className={`history-admin-badge history-badge--${tone}`}>
                      {OPERATION_TYPE_LABEL[event.action] || event.action}
                    </span>
                  </div>
                  <time
                    className="history-time-exact"
                    title={`ISO: ${event.timestamp}`}
                  >
                    <svg
                      width="13"
                      height="13"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <circle cx="12" cy="12" r="10" />
                      <polyline points="12 6 12 12 16 14" />
                    </svg>
                    {formatDateTime(event.timestamp, true)}
                  </time>
                </div>

                {/* 2. Служебные ID с быстрым копированием в буфер */}
                <div className="history-admin-meta">
                  {showUserId ? (
                    <button
                      type="button"
                      className="history-id-btn"
                      onClick={() => handleCopy(event.user_id, userCopyKey)}
                      title={`Нажмите, чтобы скопировать User ID: ${event.user_id}`}
                    >
                      <span className="history-id-btn__label">User ID:</span>
                      <span className="history-id-btn__val">
                        {event.user_id.slice(0, 8)}…{event.user_id.slice(-4)}
                      </span>
                      {copiedKey === userCopyKey ? (
                        <span className="history-id-btn__copied">Скопировано!</span>
                      ) : (
                        <CopyIcon />
                      )}
                    </button>
                  ) : null}

                  {event.target_id ? (
                    <button
                      type="button"
                      className="history-id-btn"
                      onClick={() => handleCopy(event.target_id || "", targetCopyKey)}
                      title={`Нажмите, чтобы скопировать Target ID: ${event.target_id}`}
                    >
                      <span className="history-id-btn__label">Target ID:</span>
                      <span className="history-id-btn__val">
                        {event.target_id.slice(0, 8)}…{event.target_id.slice(-4)}
                      </span>
                      {copiedKey === targetCopyKey ? (
                        <span className="history-id-btn__copied">Скопировано!</span>
                      ) : (
                        <CopyIcon />
                      )}
                    </button>
                  ) : null}

                  <button
                    type="button"
                    className="history-id-btn history-id-btn--subtle"
                    onClick={() => handleCopy(event.id, eventCopyKey)}
                    title={`Нажмите, чтобы скопировать Event TimeUUID: ${event.id}`}
                  >
                    <span className="history-id-btn__label">Event ID:</span>
                    <span className="history-id-btn__val">
                      {event.id.slice(0, 8)}…
                    </span>
                    {copiedKey === eventCopyKey ? (
                      <span className="history-id-btn__copied">Скопировано!</span>
                    ) : (
                      <CopyIcon />
                    )}
                  </button>
                </div>

                {/* 3. Опрятные плашки деталей для быстрого чтения */}
                {adminDetails.length > 0 ? (
                  <div className="history-admin-details">
                    <div className="history-chips-wrap">
                      {adminDetails.map(([key, value]) => {
                        const label = DETAIL_KEY_LABELS[key] || key;
                        const formattedVal = formatDetailValue(key, value);
                        return (
                          <span key={key} className="history-chip">
                            <span className="history-chip__key">{label}:</span>
                            <span className="history-chip__val" title={String(value)}>
                              {formattedVal}
                            </span>
                          </span>
                        );
                      })}
                    </div>

                    {/* Кнопка открытия JSON */}
                    <button
                      type="button"
                      className={`btn-json-toggle ${isJsonExpanded ? "btn-json-toggle--active" : ""}`}
                      onClick={() => toggleJson(event.id)}
                      title="Показать / скрыть JSON события"
                    >
                      <span>&#123; &#125;</span> {isJsonExpanded ? "Скрыть JSON" : "JSON"}
                    </button>
                  </div>
                ) : null}

                {/* 4. Раскрывающийся JSON блок */}
                {isJsonExpanded ? (
                  <div className="history-json-panel">
                    <div className="history-json-panel__header">
                      <span className="history-json-panel__title">
                        JSON (Apache Cassandra)
                      </span>
                      <button
                        type="button"
                        className="btn btn--ghost btn--sm history-json-copy-btn"
                        onClick={() =>
                          handleCopy(
                            JSON.stringify(event, null, 2),
                            jsonCopyKey,
                          )
                        }
                      >
                        {copiedKey === jsonCopyKey ? "✓ Скопировано!" : "Копировать JSON"}
                      </button>
                    </div>
                    <pre className="history-json-code">
                      <code>{JSON.stringify(event, null, 2)}</code>
                    </pre>
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

function CopyIcon() {
  return (
    <svg
      className="history-copy-icon"
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}
