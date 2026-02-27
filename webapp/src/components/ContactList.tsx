import { useState, useEffect, useRef } from "preact/hooks";
import { api } from "@/services/api";
import type { Contact, PaginatedResponse } from "@/types";

const PAGE_SIZE = 20;

interface ContactListProps {
  onToast: (msg: string) => void;
}

export function ContactList({ onToast }: ContactListProps) {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [tab, setTab] = useState(0); // 0=unprocessed, 1=processed, 2=all
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sort, setSort] = useState<"desc" | "asc">("desc");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [actionIds, setActionIds] = useState<Set<number>>(new Set());
  const [reloadKey, setReloadKey] = useState(0);
  const pageRef = useRef(page);
  pageRef.current = page;

  useEffect(() => {
    const controller = new AbortController();
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const offset = page * PAGE_SIZE;
        const params = new URLSearchParams();
        params.set("limit", String(PAGE_SIZE));
        params.set("offset", String(offset));
        if (tab === 0) params.set("is_processed", "false");
        else if (tab === 1) params.set("is_processed", "true");
        params.set("sort", sort);
        if (dateFrom) params.set("date_from", dateFrom);
        if (dateTo) params.set("date_to", dateTo);
        const data = await api.get<PaginatedResponse<Contact>>(
          `/contacts?${params}`,
          controller.signal,
        );
        if (!controller.signal.aborted) {
          // Clamp page if total shrank (e.g. after processing on last page)
          const maxPage = Math.max(
            0,
            Math.ceil(data.total / PAGE_SIZE) - 1,
          );
          if (pageRef.current > maxPage) {
            setPage(maxPage);
            // Don't set stale data — the re-triggered effect will fetch correct page
            return;
          }
          setContacts(data.items);
          setTotal(data.total);
        }
      } catch (e) {
        if (e instanceof DOMException && e.name === "AbortError") return;
        if (!controller.signal.aborted) {
          console.error(e);
          setError("Не удалось загрузить заявки");
        }
      }
      if (!controller.signal.aborted) setLoading(false);
    };
    fetchData();
    return () => controller.abort();
  }, [page, tab, sort, dateFrom, dateTo, reloadKey]);

  const changeTab = (newTab: number) => {
    setPage(0);
    setTab(newTab);
  };

  const toggleSort = () => {
    setPage(0);
    setSort(sort === "desc" ? "asc" : "desc");
  };

  const changeDateFrom = (value: string) => {
    setPage(0);
    setDateFrom(value);
  };

  const changeDateTo = (value: string) => {
    setPage(0);
    setDateTo(value);
  };

  const resetDates = () => {
    setPage(0);
    setDateFrom("");
    setDateTo("");
  };

  const reload = () => setReloadKey((k) => k + 1);

  const markProcessed = async (id: number) => {
    if (actionIds.has(id)) return;
    setActionIds((prev) => new Set(prev).add(id));
    try {
      await api.patch(`/contacts/${id}/process`);
      onToast("Заявка обработана");
      reload();
    } catch (e) {
      onToast((e as Error).message);
    } finally {
      setActionIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const markUnprocessed = async (id: number) => {
    if (actionIds.has(id)) return;
    setActionIds((prev) => new Set(prev).add(id));
    try {
      await api.patch(`/contacts/${id}/unprocess`);
      onToast("Заявка возвращена");
      reload();
    } catch (e) {
      onToast((e as Error).message);
    } finally {
      setActionIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="page">
      <h2>Заявки</h2>

      <div className="tabs">
        <button
          className={`tab ${tab === 0 ? "active" : ""}`}
          onClick={() => changeTab(0)}
        >
          Новые
        </button>
        <button
          className={`tab ${tab === 1 ? "active" : ""}`}
          onClick={() => changeTab(1)}
        >
          Обработанные
        </button>
        <button
          className={`tab ${tab === 2 ? "active" : ""}`}
          onClick={() => changeTab(2)}
        >
          Все
        </button>
      </div>

      <div className="filters">
        <button className="btn btn-sm" onClick={toggleSort}>
          Дата {sort === "desc" ? "↓" : "↑"}
        </button>
        <input
          type="date"
          className="filter-date"
          value={dateFrom}
          onChange={(e) =>
            changeDateFrom((e.target as HTMLInputElement).value)
          }
          placeholder="С"
        />
        <input
          type="date"
          className="filter-date"
          value={dateTo}
          onChange={(e) =>
            changeDateTo((e.target as HTMLInputElement).value)
          }
          placeholder="По"
        />
        {(dateFrom || dateTo) && (
          <button className="btn btn-sm" onClick={resetDates}>
            Сбросить
          </button>
        )}
      </div>

      {error ? (
        <div className="empty">
          <p>{error}</p>
          <button className="btn btn-sm" onClick={reload}>
            Повторить
          </button>
        </div>
      ) : (
        <>
          <div className={`card-list ${loading ? "card-list-loading" : ""}`}>
            {!loading && contacts.length === 0 && (
              <p className="empty">Нет заявок</p>
            )}
            {loading && contacts.length === 0 && (
              <div className="loading">Загрузка...</div>
            )}
            {contacts.map((c) => (
              <div key={c.id} className="card contact-card">
                <div className="card-header">
                  <span className="card-title">{c.name}</span>
                  <div className="card-header-actions">
                    {!c.is_processed ? (
                      <button
                        className="btn btn-success btn-sm"
                        disabled={actionIds.has(c.id)}
                        onClick={(e) => {
                          e.stopPropagation();
                          markProcessed(c.id);
                        }}
                      >
                        Обработать
                      </button>
                    ) : (
                      <button
                        className="btn btn-sm"
                        disabled={actionIds.has(c.id)}
                        onClick={(e) => {
                          e.stopPropagation();
                          markUnprocessed(c.id);
                        }}
                      >
                        Вернуть
                      </button>
                    )}
                  </div>
                </div>
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

          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn btn-sm"
                disabled={page === 0 || loading}
                onClick={() => setPage(page - 1)}
              >
                ←
              </button>
              <span className="pagination-info">
                {page + 1} / {totalPages}
              </span>
              <button
                className="btn btn-sm"
                disabled={page >= totalPages - 1 || loading}
                onClick={() => setPage(page + 1)}
              >
                →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
