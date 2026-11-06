import { useEffect, useRef, useState } from "react";
import { formatRuDateOnly, formatRuDateTime, parseRuDateTime } from "../lib/format";

export interface DateTimeInputProps {
  value: string; // "DD.MM.YYYY" or "DD.MM.YYYY HH:mm"
  onChange: (value: string) => void;
  mode?: "date" | "datetime";
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  id?: string;
}

const MONTH_NAMES = [
  "Январь",
  "Февраль",
  "Март",
  "Апрель",
  "Май",
  "Июнь",
  "Июль",
  "Август",
  "Сентябрь",
  "Октябрь",
  "Ноябрь",
  "Декабрь",
];

const WEEK_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

function formatMask(raw: string, mode: "date" | "datetime"): string {
  const isDateOnly = mode === "date";
  const maxDigits = isDateOnly ? 8 : 12;
  const digits = raw.replace(/\D/g, "").slice(0, maxDigits);
  let result = "";
  if (digits.length > 0) {
    result += digits.slice(0, 2);
  }
  if (digits.length > 2) {
    result += "." + digits.slice(2, 4);
  }
  if (digits.length > 4) {
    result += "." + digits.slice(4, 8);
  }
  if (!isDateOnly) {
    if (digits.length > 8) {
      result += " " + digits.slice(8, 10);
    }
    if (digits.length > 10) {
      result += ":" + digits.slice(10, 12);
    }
  }
  return result;
}

export function CalendarIcon({ size = 18 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      style={{ display: "block" }}
    >
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  );
}

export function DateTimeInput({
  value,
  onChange,
  mode = "datetime",
  placeholder,
  disabled = false,
  className = "",
  id,
}: DateTimeInputProps) {
  const isDateOnly = mode === "date";
  const defaultPlaceholder = isDateOnly ? "ДД.ММ.ГГГГ" : "ДД.ММ.ГГГГ ЧЧ:ММ";
  const maxLength = isDateOnly ? 10 : 16;

  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Calendar view state (year & month)
  const parsedDate = parseRuDateTime(value);
  const [viewDate, setViewDate] = useState(() => parsedDate || new Date());

  // Hours & minutes state for picker
  const [selectedHour, setSelectedHour] = useState(() =>
    parsedDate ? String(parsedDate.getHours()).padStart(2, "0") : "12",
  );
  const [selectedMinute, setSelectedMinute] = useState(() =>
    parsedDate ? String(parsedDate.getMinutes()).padStart(2, "0") : "00",
  );

  // Keep viewDate in sync when value changes to a valid date
  useEffect(() => {
    if (parsedDate) {
      setViewDate(parsedDate);
      setSelectedHour(String(parsedDate.getHours()).padStart(2, "0"));
      setSelectedMinute(String(parsedDate.getMinutes()).padStart(2, "0"));
    }
  }, [value]);

  // Close calendar popup on click outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const nextVal = e.target.value;
    // If user is clearing
    if (!nextVal) {
      onChange("");
      return;
    }

    // If deleting last character that was a separator, handle naturally
    if (nextVal.length < value.length) {
      onChange(nextVal);
      return;
    }

    // Auto-mask
    const masked = formatMask(nextVal, mode);
    onChange(masked);
  }

  function handlePrevMonth() {
    setViewDate(
      new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1),
    );
  }

  function handleNextMonth() {
    setViewDate(
      new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1),
    );
  }

  function handleSelectDay(day: number) {
    const year = viewDate.getFullYear();
    const month = viewDate.getMonth();
    if (isDateOnly) {
      const d = new Date(year, month, day);
      onChange(formatRuDateOnly(d));
      setIsOpen(false);
      return;
    }
    const h = parseInt(selectedHour, 10) || 0;
    const m = parseInt(selectedMinute, 10) || 0;
    const d = new Date(year, month, day, h, m);
    onChange(formatRuDateTime(d));
  }

  function handleSetToday() {
    const now = new Date();
    setViewDate(now);
    if (isDateOnly) {
      onChange(formatRuDateOnly(now));
      setIsOpen(false);
      return;
    }
    setSelectedHour(String(now.getHours()).padStart(2, "0"));
    setSelectedMinute(String(now.getMinutes()).padStart(2, "0"));
    onChange(formatRuDateTime(now));
    setIsOpen(false);
  }

  function handleSetEndOfDay() {
    const base = parsedDate || viewDate;
    const d = new Date(base.getFullYear(), base.getMonth(), base.getDate(), 23, 59);
    setSelectedHour("23");
    setSelectedMinute("59");
    onChange(formatRuDateTime(d));
  }

  function handleSetStartOfDay() {
    const base = parsedDate || viewDate;
    const d = new Date(base.getFullYear(), base.getMonth(), base.getDate(), 0, 0);
    setSelectedHour("00");
    setSelectedMinute("00");
    onChange(formatRuDateTime(d));
  }

  function handleTimeChange(h: string, m: string) {
    setSelectedHour(h);
    setSelectedMinute(m);
    const base = parsedDate || viewDate;
    const hourNum = parseInt(h, 10) || 0;
    const minNum = parseInt(m, 10) || 0;
    const d = new Date(base.getFullYear(), base.getMonth(), base.getDate(), hourNum, minNum);
    onChange(formatRuDateTime(d));
  }

  // Generate calendar days
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const firstDayOfWeek = (new Date(year, month, 1).getDay() + 6) % 7; // Monday = 0
  const daysInCurrentMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrevMonth = new Date(year, month, 0).getDate();

  const isSelected = (day: number) => {
    if (!parsedDate) return false;
    return (
      parsedDate.getFullYear() === year &&
      parsedDate.getMonth() === month &&
      parsedDate.getDate() === day
    );
  };

  const isToday = (day: number) => {
    const now = new Date();
    return (
      now.getFullYear() === year &&
      now.getMonth() === month &&
      now.getDate() === day
    );
  };

  const isComplete = value.length === maxLength;
  const isInvalid = isComplete && !parsedDate;

  return (
    <div
      ref={containerRef}
      className={`ru-datetime-wrapper ${className}`}
      style={{ position: "relative", width: "100%" }}
    >
      <div
        className={`ru-datetime-box ${isInvalid ? "is-invalid" : ""}`}
        style={{
          display: "flex",
          alignItems: "center",
          position: "relative",
          width: "100%",
        }}
      >
        <input
          id={id}
          type="text"
          value={value}
          onChange={handleInputChange}
          placeholder={placeholder || defaultPlaceholder}
          disabled={disabled}
          maxLength={maxLength}
          style={{
            width: "100%",
            height: "44px",
            padding: "0 68px 0 12px",
            border: isInvalid
              ? "1px solid var(--danger, #b91c1c)"
              : "1px solid var(--line, #e7e5e4)",
            borderRadius: "10px",
            background: "#fff",
            color: "var(--ink, #1c1917)",
            fontSize: "14px",
            fontFamily: "inherit",
          }}
        />

        <div
          style={{
            position: "absolute",
            right: "8px",
            display: "flex",
            alignItems: "center",
            gap: "4px",
          }}
        >
          {value ? (
            <button
              type="button"
              onClick={() => onChange("")}
              title="Очистить"
              style={{
                background: "transparent",
                border: "none",
                cursor: "pointer",
                padding: "4px",
                fontSize: "16px",
                color: "var(--muted, #78716c)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                lineHeight: 1,
              }}
            >
              ×
            </button>
          ) : null}

          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            disabled={disabled}
            title="Открыть календарь"
            style={{
              background: "transparent",
              border: "none",
              cursor: "pointer",
              padding: "6px",
              lineHeight: 1,
              borderRadius: "6px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: isOpen ? "var(--accent, #0f766e)" : "var(--muted, #78716c)",
              transition: "color 0.15s ease",
            }}
          >
            <CalendarIcon size={18} />
          </button>
        </div>
      </div>

      {isOpen ? (
        <div
          className="card ru-datetime-popup"
          style={{
            position: "absolute",
            top: "calc(100% + 6px)",
            left: 0,
            zIndex: 100,
            background: "var(--surface, #fffdf8)",
            border: "1px solid var(--line, #e7e5e4)",
            borderRadius: "var(--radius, 12px)",
            boxShadow: "0 10px 25px rgba(0,0,0,0.12)",
            padding: "14px",
            width: "290px",
          }}
        >
          {/* Header */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "10px",
            }}
          >
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              onClick={handlePrevMonth}
              style={{ padding: "4px 8px" }}
            >
              ‹
            </button>
            <strong style={{ fontSize: "14px" }}>
              {MONTH_NAMES[month]} {year}
            </strong>
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              onClick={handleNextMonth}
              style={{ padding: "4px 8px" }}
            >
              ›
            </button>
          </div>

          {/* Weekday headers */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(7, 1fr)",
              textAlign: "center",
              fontSize: "11px",
              fontWeight: 600,
              color: "var(--muted, #78716c)",
              marginBottom: "6px",
            }}
          >
            {WEEK_DAYS.map((w) => (
              <span key={w}>{w}</span>
            ))}
          </div>

          {/* Days grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(7, 1fr)",
              gap: "2px",
              textAlign: "center",
            }}
          >
            {/* Prev month fill */}
            {Array.from({ length: firstDayOfWeek }).map((_, i) => (
              <span
                key={`prev-${i}`}
                style={{
                  padding: "6px 0",
                  fontSize: "12px",
                  color: "#cbd5e1",
                  userSelect: "none",
                }}
              >
                {daysInPrevMonth - firstDayOfWeek + i + 1}
              </span>
            ))}

            {/* Current month days */}
            {Array.from({ length: daysInCurrentMonth }).map((_, i) => {
              const day = i + 1;
              const selected = isSelected(day);
              const today = isToday(day);
              return (
                <button
                  key={`day-${day}`}
                  type="button"
                  onClick={() => handleSelectDay(day)}
                  style={{
                    background: selected
                      ? "var(--accent, #0f766e)"
                      : today
                        ? "rgba(15, 118, 110, 0.1)"
                        : "transparent",
                    color: selected ? "#fff" : "var(--ink, #1c1917)",
                    border: today && !selected ? "1px solid var(--accent, #0f766e)" : "none",
                    borderRadius: "6px",
                    padding: "6px 0",
                    fontSize: "13px",
                    fontWeight: selected || today ? 600 : 400,
                    cursor: "pointer",
                    transition: "background 0.15s ease",
                  }}
                >
                  {day}
                </button>
              );
            })}
          </div>

          {/* Time picker section (only in datetime mode) */}
          {!isDateOnly ? (
            <>
              <div
                style={{
                  marginTop: "12px",
                  paddingTop: "10px",
                  borderTop: "1px solid var(--line, #e7e5e4)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <span style={{ fontSize: "12px", color: "var(--muted, #78716c)" }}>
                  Время:
                </span>
                <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <select
                    value={selectedHour}
                    onChange={(e) => handleTimeChange(e.target.value, selectedMinute)}
                    style={{
                      height: "32px",
                      padding: "0 6px",
                      fontSize: "13px",
                      borderRadius: "6px",
                      border: "1px solid var(--line, #e7e5e4)",
                      background: "#fff",
                    }}
                  >
                    {Array.from({ length: 24 }).map((_, h) => {
                      const val = String(h).padStart(2, "0");
                      return (
                        <option key={val} value={val}>
                          {val}
                        </option>
                      );
                    })}
                  </select>
                  <span>:</span>
                  <select
                    value={selectedMinute}
                    onChange={(e) => handleTimeChange(selectedHour, e.target.value)}
                    style={{
                      height: "32px",
                      padding: "0 6px",
                      fontSize: "13px",
                      borderRadius: "6px",
                      border: "1px solid var(--line, #e7e5e4)",
                      background: "#fff",
                    }}
                  >
                    {Array.from({ length: 60 }).map((_, m) => {
                      const val = String(m).padStart(2, "0");
                      return (
                        <option key={val} value={val}>
                          {val}
                        </option>
                      );
                    })}
                  </select>
                </div>
              </div>

              {/* Quick time chips */}
              <div
                style={{
                  display: "flex",
                  gap: "4px",
                  marginTop: "8px",
                  flexWrap: "wrap",
                }}
              >
                <button
                  type="button"
                  className="btn btn--ghost btn--sm"
                  onClick={handleSetStartOfDay}
                  style={{ fontSize: "11px", padding: "2px 6px" }}
                >
                  00:00
                </button>
                <button
                  type="button"
                  className="btn btn--ghost btn--sm"
                  onClick={() => handleTimeChange("12", "00")}
                  style={{ fontSize: "11px", padding: "2px 6px" }}
                >
                  12:00
                </button>
                <button
                  type="button"
                  className="btn btn--ghost btn--sm"
                  onClick={handleSetEndOfDay}
                  style={{ fontSize: "11px", padding: "2px 6px" }}
                >
                  23:59
                </button>
                <button
                  type="button"
                  className="btn btn--ghost btn--sm"
                  onClick={handleSetToday}
                  style={{ fontSize: "11px", padding: "2px 6px" }}
                >
                  Сейчас
                </button>
              </div>
            </>
          ) : null}

          {/* Action buttons */}
          <div
            style={{
              marginTop: "12px",
              paddingTop: "8px",
              borderTop: "1px solid var(--line, #e7e5e4)",
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              onClick={handleSetToday}
              style={{ fontSize: "12px" }}
            >
              Сегодня
            </button>
            <div style={{ display: "flex", gap: "6px" }}>
              <button
                type="button"
                className="btn btn--ghost btn--sm"
                onClick={() => {
                  onChange("");
                  setIsOpen(false);
                }}
                style={{ fontSize: "12px" }}
              >
                Сбросить
              </button>
              <button
                type="button"
                className="btn btn--primary btn--sm"
                onClick={() => setIsOpen(false)}
                style={{ fontSize: "12px" }}
              >
                Готово
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
