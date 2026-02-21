import { useState, useEffect } from "preact/hooks";
import { api } from "@/services/api";
import type { Event, EntityStatus, PaginatedResponse } from "@/types";

const STATUS_LABELS: Record<EntityStatus, string> = {
  draft: "Черновик",
  published: "Опубликовано",
  cancelled: "Отменено",
  archived: "Архив",
};

const STATUS_TABS: (EntityStatus | null)[] = [
  null,
  "draft",
  "published",
  "cancelled",
  "archived",
];
const TAB_LABELS = ["Все", "Черновики", "Опубликованные", "Отменённые", "Архив"];

interface EventListProps {
  onNavigate: (path: string) => void;
}

export function EventList({ onNavigate }: EventListProps) {
  const [events, setEvents] = useState<Event[]>([]);
  const [_total, setTotal] = useState(0);
  const [tab, setTab] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const status = STATUS_TABS[tab];
      let path = `/events?limit=50`;
      if (status) path += `&status=${status}`;
      if (search) path += `&search=${encodeURIComponent(search)}`;
      const data = await api.get<PaginatedResponse<Event>>(path);
      setEvents(data.items);
      setTotal(data.total);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, [tab, search]);

  return (
    <div className="page">
      <div className="page-header">
        <h2>Мероприятия</h2>
        <button
          className="btn btn-primary"
          onClick={() => onNavigate("/events/new")}
        >
          + Создать
        </button>
      </div>

      <div className="tabs">
        {TAB_LABELS.map((label, i) => (
          <button
            key={i}
            className={`tab ${tab === i ? "active" : ""}`}
            onClick={() => setTab(i)}
          >
            {label}
          </button>
        ))}
      </div>

      <input
        className="search-input"
        type="text"
        placeholder="Поиск..."
        value={search}
        onInput={(e) => setSearch((e.target as HTMLInputElement).value)}
      />

      {loading ? (
        <div className="loading">Загрузка...</div>
      ) : (
        <div className="card-list">
          {events.length === 0 && <p className="empty">Нет мероприятий</p>}
          {events.map((event) => (
            <div
              key={event.id}
              className="card"
              onClick={() => onNavigate("/events/" + event.id)}
            >
              <div className="card-header">
                <span className="card-title">{event.title}</span>
                <span className={`status-badge status-${event.status}`}>
                  {STATUS_LABELS[event.status]}
                </span>
              </div>
              <div className="card-meta">
                {event.event_date || ""} {event.event_time || ""}
                {event.location ? ` · ${event.location}` : ""}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
