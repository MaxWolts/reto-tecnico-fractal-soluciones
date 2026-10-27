import { useEffect, useId, useRef, useState } from "react";
import { COMPACT_QUERY } from "../breakpoints";
import { MAX_DATE, MIN_DATE, isValidDate } from "../dates";
import { useMediaQuery } from "../hooks/useMediaQuery";
import {
  PRIORITIES,
  STATUSES,
  type Operator,
  type Priority,
  type TicketFilters,
  type TicketStatus,
} from "../types";
import { PRIORITY_LABEL, STATUS_LABEL } from "../utils";
import "./FiltersBar.css";

interface FiltersBarProps {
  filters: TicketFilters;
  operators: Operator[];
  onChange: (patch: Partial<TicketFilters>) => void;
  onClear: () => void;
}

const DEBOUNCE_MS = 300;

export function FiltersBar({
  filters,
  operators,
  onChange,
  onClear,
}: FiltersBarProps) {
  const [query, setQuery] = useState(filters.q ?? "");
  const filtersQ = useRef(filters.q);
  useEffect(() => {
    filtersQ.current = filters.q;
  });

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed === (filtersQ.current ?? "")) return;
    const timer = window.setTimeout(
      () => onChange({ q: trimmed || undefined }),
      DEBOUNCE_MS,
    );
    return () => window.clearTimeout(timer);
  }, [query, onChange]);

  const active = Object.keys(filters).length > 0 || query !== "";
  const compact = useMediaQuery(COMPACT_QUERY);
  const [open, setOpen] = useState(false);
  const panelId = useId();
  // The search box is always visible, so it is not counted in the badge.
  const activeCount = Object.keys(filters).filter((k) => k !== "q").length;

  // Empty clears the filter; partial, out-of-range or impossible dates are ignored.
  function onDateChange(key: "from" | "to", value: string) {
    if (value === "") onChange({ [key]: undefined });
    else if (isValidDate(value)) onChange({ [key]: value });
  }

  return (
    <form
      className="filters"
      role="search"
      aria-label="Filter tickets"
      onSubmit={(e) => e.preventDefault()}
    >
      <label className="filters__field filters__field--search">
        <span className="filters__label">Search</span>
        <input
          type="search"
          className="filters__input"
          placeholder="Title, asset or #code"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </label>
      {compact && (
        <button
          type="button"
          className="filters__toggle"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => setOpen((v) => !v)}
        >
          Filters
          {activeCount > 0 && (
            <span className="filters__badge">
              {activeCount}
              <span className="filters__sr"> active</span>
            </span>
          )}
        </button>
      )}
      <div id={panelId} className="filters__panel" hidden={compact && !open}>
        <label className="filters__field">
          <span className="filters__label">Status</span>
          <select
            className="filters__input"
            value={filters.status ?? ""}
            onChange={(e) =>
              onChange({
                status: (e.target.value || undefined) as
                  TicketStatus | undefined,
              })
            }
          >
            <option value="">All</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {STATUS_LABEL[s]}
              </option>
            ))}
          </select>
        </label>
        <label className="filters__field">
          <span className="filters__label">Priority</span>
          <select
            className="filters__input"
            value={filters.priority ?? ""}
            onChange={(e) =>
              onChange({
                priority: (e.target.value || undefined) as Priority | undefined,
              })
            }
          >
            <option value="">All</option>
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {PRIORITY_LABEL[p]}
              </option>
            ))}
          </select>
        </label>
        <label className="filters__field">
          <span className="filters__label">Operator</span>
          <select
            className="filters__input"
            value={filters.operatorId ?? ""}
            onChange={(e) =>
              onChange({
                operatorId: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          >
            <option value="">All</option>
            {operators.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>
        </label>
        <label className="filters__field">
          <span className="filters__label">From</span>
          <input
            type="date"
            className="filters__input"
            value={filters.from ?? ""}
            min={MIN_DATE}
            max={filters.to ?? MAX_DATE}
            onChange={(e) => onDateChange("from", e.target.value)}
          />
        </label>
        <label className="filters__field">
          <span className="filters__label">To</span>
          <input
            type="date"
            className="filters__input"
            value={filters.to ?? ""}
            min={filters.from ?? MIN_DATE}
            max={MAX_DATE}
            onChange={(e) => onDateChange("to", e.target.value)}
          />
        </label>
        <button
          type="button"
          className="filters__clear"
          disabled={!active}
          onClick={() => {
            setQuery("");
            onClear();
          }}
        >
          Clear filters
        </button>
      </div>
    </form>
  );
}
