import { useState, useEffect } from "preact/hooks";
import { api } from "@/services/api";
import type { User, NewUserFormData } from "@/types";

const tg = window.Telegram?.WebApp;

interface UserListProps {
  onToast: (msg: string) => void;
}

export function UserList({ onToast }: UserListProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [newUser, setNewUser] = useState<NewUserFormData>({
    telegram_id: "",
    username: "",
    first_name: "",
  });

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get<User[]>("/users");
      setUsers(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const addUser = async () => {
    if (!newUser.telegram_id) {
      onToast("Укажите Telegram ID");
      return;
    }
    try {
      await api.post("/users", {
        telegram_id: parseInt(newUser.telegram_id),
        username: newUser.username || null,
        first_name: newUser.first_name || null,
      });
      onToast("Пользователь добавлен");
      setNewUser({ telegram_id: "", username: "", first_name: "" });
      setShowForm(false);
      load();
    } catch (e) {
      onToast((e as Error).message);
    }
  };

  const removeUser = async (userId: number) => {
    const doRemove = async () => {
      try {
        await api.delete(`/users/${userId}`);
        onToast("Пользователь удалён");
        load();
      } catch (e) {
        onToast((e as Error).message);
      }
    };
    if (tg) {
      tg.showConfirm("Удалить пользователя?", (ok) => {
        if (ok) doRemove();
      });
    } else {
      if (confirm("Удалить пользователя?")) doRemove();
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h2>Пользователи</h2>
        <button
          className="btn btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? "Отмена" : "+ Добавить"}
        </button>
      </div>

      {showForm && (
        <div className="form add-user-form">
          <label className="form-label">
            Telegram ID *
            <input
              className="form-input"
              type="number"
              value={newUser.telegram_id}
              onInput={(e) =>
                setNewUser((u) => ({
                  ...u,
                  telegram_id: (e.target as HTMLInputElement).value,
                }))
              }
              placeholder="123456789"
            />
          </label>
          <label className="form-label">
            Username
            <input
              className="form-input"
              type="text"
              value={newUser.username}
              onInput={(e) =>
                setNewUser((u) => ({
                  ...u,
                  username: (e.target as HTMLInputElement).value,
                }))
              }
              placeholder="@username"
            />
          </label>
          <label className="form-label">
            Имя
            <input
              className="form-input"
              type="text"
              value={newUser.first_name}
              onInput={(e) =>
                setNewUser((u) => ({
                  ...u,
                  first_name: (e.target as HTMLInputElement).value,
                }))
              }
              placeholder="Имя"
            />
          </label>
          <button className="btn btn-success" onClick={addUser}>
            Добавить
          </button>
        </div>
      )}

      {loading ? (
        <div className="loading">Загрузка...</div>
      ) : (
        <div className="card-list">
          {users.length === 0 && <p className="empty">Нет пользователей</p>}
          {users.map((u) => (
            <div key={u.id} className="card user-card">
              <div className="card-header">
                <span className="card-title">
                  {u.first_name || ""} {u.last_name || ""}
                  {u.username && (
                    <span className="card-meta"> @{u.username}</span>
                  )}
                </span>
              </div>
              <div className="card-meta">
                ID: {u.telegram_id} · Добавлен:{" "}
                {new Date(u.created_at).toLocaleDateString("ru")}
              </div>
              <button
                className="btn btn-danger btn-sm"
                onClick={(e) => {
                  e.stopPropagation();
                  removeUser(u.id);
                }}
              >
                Удалить
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
