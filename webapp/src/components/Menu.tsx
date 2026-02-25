import { useState } from "preact/hooks";
import { api } from "../services/api";

function navigate(path: string) {
  window.location.hash = path;
}

interface MenuProps {
  onToast: (msg: string) => void;
}

export function Menu({ onToast }: MenuProps) {
  const [syncing, setSyncing] = useState(false);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await api.post("/sync");
      onToast("Сайт обновлён");
    } catch (err: any) {
      onToast(err.message || "Ошибка синхронизации");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="menu">
      <h1 className="menu-title">KomonBot</h1>
      <div className="menu-grid">
        <button className="menu-btn" onClick={() => navigate("/events")}>
          <span className="menu-btn-icon">📅</span>
          <span>Мероприятия</span>
        </button>
        <button className="menu-btn" onClick={() => navigate("/courses")}>
          <span className="menu-btn-icon">📚</span>
          <span>Курсы</span>
        </button>
        <button className="menu-btn" onClick={() => navigate("/contacts")}>
          <span className="menu-btn-icon">📩</span>
          <span>Заявки</span>
        </button>
        <button className="menu-btn" onClick={() => navigate("/users")}>
          <span className="menu-btn-icon">👥</span>
          <span>Пользователи</span>
        </button>
      </div>
      <button
        className="btn btn-primary sync-btn"
        onClick={handleSync}
        disabled={syncing}
      >
        {syncing ? "Синхронизация..." : "🔄 Обновить сайт"}
      </button>
    </div>
  );
}
