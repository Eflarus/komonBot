import { useState, useEffect } from "preact/hooks";
import { api } from "@/services/api";
import type { Contact, PaginatedResponse } from "@/types";

interface ContactListProps {
  onToast: (msg: string) => void;
}

export function ContactList({ onToast }: ContactListProps) {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [tab, setTab] = useState(0); // 0=unprocessed, 1=processed, 2=all
  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState<"desc" | "asc">("desc");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      let path = "/contacts?limit=50";
      if (tab === 0) path += "&is_processed=false";
      else if (tab === 1) path += "&is_processed=true";
      path += `&sort=${sort}`;
      if (dateFrom) path += `&date_from=${dateFrom}`;
      if (dateTo) path += `&date_to=${dateTo}`;
      const data = await api.get<PaginatedResponse<Contact>>(path);
      setContacts(data.items);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, [tab, sort, dateFrom, dateTo]);

  const markProcessed = async (id: number) => {
    try {
      await api.patch(`/contacts/${id}/process`);
      onToast("Заявка обработана");
      load();
    } catch (e) {
      onToast((e as Error).message);
    }
  };

  const markUnprocessed = async (id: number) => {
    try {
      await api.patch(`/contacts/${id}/unprocess`);
      onToast("Заявка возвращена");
      load();
    } catch (e) {
      onToast((e as Error).message);
    }
  };

  return (
    <div className="page">
      <h2>Заявки</h2>

      <div className="tabs">
        <button
          className={`tab ${tab === 0 ? "active" : ""}`}
          onClick={() => setTab(0)}
        >
          Новые
        </button>
        <button
          className={`tab ${tab === 1 ? "active" : ""}`}
          onClick={() => setTab(1)}
        >
          Обработанные
        </button>
        <button
          className={`tab ${tab === 2 ? "active" : ""}`}
          onClick={() => setTab(2)}
        >
          Все
        </button>
      </div>

      <div className="filters">
        <button
          className="btn btn-sm"
          onClick={() => setSort(sort === "desc" ? "asc" : "desc")}
        >
          Дата {sort === "desc" ? "↓" : "↑"}
        </button>
        <input
          type="date"
          className="filter-date"
          value={dateFrom}
          onChange={(e) => setDateFrom((e.target as HTMLInputElement).value)}
          placeholder="С"
        />
        <input
          type="date"
          className="filter-date"
          value={dateTo}
          onChange={(e) => setDateTo((e.target as HTMLInputElement).value)}
          placeholder="По"
        />
        {(dateFrom || dateTo) && (
          <button
            className="btn btn-sm"
            onClick={() => {
              setDateFrom("");
              setDateTo("");
            }}
          >
            Сбросить
          </button>
        )}
      </div>

      {loading ? (
        <div className="loading">Загрузка...</div>
      ) : (
        <div className="card-list">
          {contacts.length === 0 && <p className="empty">Нет заявок</p>}
          {contacts.map((c) => (
            <div key={c.id} className="card contact-card">
              <div className="card-header">
                <span className="card-title">{c.name}</span>
                <span
                  className={`status-badge ${c.is_processed ? "status-archived" : "status-draft"}`}
                >
                  {c.is_processed ? "Обработана" : "Новая"}
                </span>
              </div>
              {!c.is_processed && (
                <button
                  className="btn btn-success btn-sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    markProcessed(c.id);
                  }}
                >
                  Обработать
                </button>
              )}
              {c.is_processed && (
                <button
                  className="btn btn-sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    markUnprocessed(c.id);
                  }}
                >
                  Вернуть
                </button>
              )}
              <div className="card-meta">
                <div>Тел: {c.phone}</div>
                {c.email && <div>Email: {c.email}</div>}
                {c.source && <div>Источник: {c.source}</div>}
              </div>
              <div className="card-body">{c.message}</div>
              <div className="card-meta">
                {new Date(c.created_at).toLocaleString("ru")}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
