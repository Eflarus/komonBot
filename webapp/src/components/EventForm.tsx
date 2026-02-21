import { useState, useEffect } from "preact/hooks";
import { api } from "@/services/api";
import type { Event, EventFormData, EntityStatus } from "@/types";

const tg = window.Telegram?.WebApp;
const DRAFT_KEY = "komonbot_event_draft";

function loadDraft(): Partial<EventFormData> {
  try {
    return JSON.parse(localStorage.getItem(DRAFT_KEY) || "{}");
  } catch {
    return {};
  }
}
function saveDraft(data: EventFormData) {
  localStorage.setItem(DRAFT_KEY, JSON.stringify(data));
}
function clearDraft() {
  localStorage.removeItem(DRAFT_KEY);
}

interface EventFormProps {
  id?: string;
  onNavigate: (path: string) => void;
  onToast: (msg: string) => void;
}

export function EventForm({ id, onNavigate, onToast }: EventFormProps) {
  const isNew = !id;
  const [form, setForm] = useState<EventFormData>({
    title: "",
    description: "",
    location: "",
    event_date: "",
    event_time: "",
    ticket_link: "",
    order: 0,
  });
  const [status, setStatus] = useState<EntityStatus>("draft");
  const [coverImage, setCoverImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isNew) {
      const draft = loadDraft();
      if (draft.title) setForm((f) => ({ ...f, ...draft }));
    } else {
      api
        .get<Event>(`/events/${id}`)
        .then((data) => {
          setForm({
            title: data.title || "",
            description: data.description || "",
            location: data.location || "",
            event_date: data.event_date || "",
            event_time: data.event_time ? data.event_time.slice(0, 5) : "",
            ticket_link: data.ticket_link || "",
            order: data.order || 0,
          });
          setStatus(data.status);
          setCoverImage(data.cover_image);
          setLoading(false);
        })
        .catch((e: Error) => {
          onToast(e.message);
          setLoading(false);
        });
    }
  }, [id]);

  useEffect(() => {
    if (isNew) saveDraft(form);
  }, [form, isNew]);

  const update =
    (field: keyof EventFormData) => (e: { target: EventTarget | null }) => {
      setForm((f) => ({
        ...f,
        [field]: (e.target as HTMLInputElement).value,
      }));
    };

  const save = async () => {
    setSaving(true);
    try {
      if (isNew) {
        const data = await api.post<Event>("/events", form);
        clearDraft();
        onToast("Мероприятие создано");
        onNavigate(`/events/${data.id}`);
      } else {
        await api.patch(`/events/${id}`, form);
        onToast("Сохранено");
      }
    } catch (e) {
      onToast((e as Error).message);
    }
    setSaving(false);
  };

  const publish = async () => {
    try {
      await api.post(`/events/${id}/publish`);
      setStatus("published");
      onToast("Опубликовано");
    } catch (e) {
      onToast((e as Error).message);
    }
  };

  const unpublish = async () => {
    try {
      await api.post(`/events/${id}/unpublish`);
      setStatus("draft");
      onToast("Снято с публикации");
    } catch (e) {
      onToast((e as Error).message);
    }
  };

  const cancel = async () => {
    try {
      await api.post(`/events/${id}/cancel`);
      setStatus("cancelled");
      onToast("Отменено");
    } catch (e) {
      onToast((e as Error).message);
    }
  };

  const remove = async () => {
    const doDelete = async () => {
      try {
        await api.delete(`/events/${id}`);
        onToast("Удалено");
        onNavigate("/events");
      } catch (e) {
        onToast((e as Error).message);
      }
    };
    if (tg) {
      tg.showConfirm("Удалить мероприятие?", (ok) => {
        if (ok) doDelete();
      });
    } else {
      if (confirm("Удалить мероприятие?")) doDelete();
    }
  };

  const uploadImage = async (e: globalThis.Event) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    try {
      const data = await api.uploadFile<{ url: string }>(
        `/events/${id}/upload-image`,
        file,
      );
      setCoverImage(data.url);
      onToast("Изображение загружено");
    } catch (err) {
      onToast((err as Error).message);
    }
  };

  if (loading) return <div className="loading">Загрузка...</div>;

  return (
    <div className="page">
      <h2>{isNew ? "Новое мероприятие" : "Редактирование"}</h2>

      <div className="form">
        <label className="form-label">
          Название *
          <input
            className="form-input"
            type="text"
            value={form.title}
            onInput={update("title")}
            placeholder="Название"
          />
        </label>

        <label className="form-label">
          Описание
          <textarea
            className="form-textarea"
            value={form.description}
            onInput={update("description")}
            rows={3}
            placeholder="Описание (внутренние заметки)"
          />
        </label>

        <label className="form-label">
          Место *
          <input
            className="form-input"
            type="text"
            value={form.location}
            onInput={update("location")}
            placeholder="Место проведения"
          />
        </label>

        <div className="form-row">
          <label className="form-label">
            Дата *
            <input
              className="form-input"
              type="date"
              value={form.event_date}
              onInput={update("event_date")}
            />
          </label>
          <label className="form-label">
            Время *
            <input
              className="form-input"
              type="time"
              value={form.event_time}
              onInput={update("event_time")}
            />
          </label>
        </div>

        <label className="form-label">
          Ссылка на билеты
          <input
            className="form-input"
            type="url"
            value={form.ticket_link}
            onInput={update("ticket_link")}
            placeholder="https://..."
          />
        </label>

        <label className="form-label">
          Порядок отображения
          <input
            className="form-input"
            type="number"
            value={form.order}
            onInput={update("order")}
            min={0}
          />
        </label>

        {!isNew && (
          <>
            <label className="form-label">
              Обложка (516x516)
              <input
                className="form-input"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={uploadImage}
              />
            </label>
            {coverImage && (
              <img className="preview-image" src={coverImage} alt="Cover" />
            )}
          </>
        )}

        <div className="form-actions">
          <button className="btn btn-primary" onClick={save} disabled={saving}>
            {saving ? "Сохранение..." : "Сохранить"}
          </button>

          {!isNew && (
            <>
              {status === "draft" && (
                <button className="btn btn-success" onClick={publish}>
                  Опубликовать
                </button>
              )}
              {status === "published" && (
                <>
                  <button className="btn btn-warning" onClick={unpublish}>
                    Снять
                  </button>
                  <button className="btn btn-danger" onClick={cancel}>
                    Отменить
                  </button>
                </>
              )}
              {status !== "published" && (
                <button className="btn btn-danger" onClick={remove}>
                  Удалить
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
