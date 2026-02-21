import { useState, useEffect } from "preact/hooks";
import { api } from "@/services/api";
import type { Course, CourseFormData, EntityStatus } from "@/types";

const tg = window.Telegram?.WebApp;
const DRAFT_KEY = "komonbot_course_draft";

function loadDraft(): Partial<CourseFormData> {
  try {
    return JSON.parse(localStorage.getItem(DRAFT_KEY) || "{}");
  } catch {
    return {};
  }
}
function saveDraft(data: CourseFormData) {
  localStorage.setItem(DRAFT_KEY, JSON.stringify(data));
}
function clearDraft() {
  localStorage.removeItem(DRAFT_KEY);
}

interface CourseFormProps {
  id?: string;
  onNavigate: (path: string) => void;
  onToast: (msg: string) => void;
}

export function CourseForm({ id, onNavigate, onToast }: CourseFormProps) {
  const isNew = !id;
  const [form, setForm] = useState<CourseFormData>({
    title: "",
    description: "",
    detailed_description: "",
    schedule: "",
    cost: "0",
    currency: "RUB",
    order: 0,
  });
  const [status, setStatus] = useState<EntityStatus>("draft");
  const [imageDesktop, setImageDesktop] = useState<string | null>(null);
  const [imageMobile, setImageMobile] = useState<string | null>(null);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isNew) {
      const draft = loadDraft();
      if (draft.title) setForm((f) => ({ ...f, ...draft }));
    } else {
      api
        .get<Course>(`/courses/${id}`)
        .then((data) => {
          setForm({
            title: data.title || "",
            description: data.description || "",
            detailed_description: data.detailed_description || "",
            schedule: data.schedule || "",
            cost: String(data.cost || 0),
            currency: data.currency || "RUB",
            order: data.order || 0,
          });
          setStatus(data.status);
          setImageDesktop(data.image_desktop);
          setImageMobile(data.image_mobile);
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
    (field: keyof CourseFormData) => (e: { target: EventTarget | null }) => {
      setForm((f) => ({
        ...f,
        [field]: (e.target as HTMLInputElement).value,
      }));
    };

  const save = async () => {
    setSaving(true);
    try {
      const payload = { ...form, cost: parseFloat(form.cost) || 0 };
      if (isNew) {
        const data = await api.post<Course>("/courses", payload);
        clearDraft();
        onToast("Курс создан");
        onNavigate(`/courses/${data.id}`);
      } else {
        await api.patch(`/courses/${id}`, payload);
        onToast("Сохранено");
      }
    } catch (e) {
      onToast((e as Error).message);
    }
    setSaving(false);
  };

  const publish = async () => {
    try {
      await api.post(`/courses/${id}/publish`);
      setStatus("published");
      onToast("Опубликовано");
    } catch (e) {
      onToast((e as Error).message);
    }
  };

  const unpublish = async () => {
    try {
      await api.post(`/courses/${id}/unpublish`);
      setStatus("draft");
      onToast("Снято с публикации");
    } catch (e) {
      onToast((e as Error).message);
    }
  };

  const cancel = async () => {
    try {
      await api.post(`/courses/${id}/cancel`);
      setStatus("cancelled");
      onToast("Отменено");
    } catch (e) {
      onToast((e as Error).message);
    }
  };

  const remove = async () => {
    const doDelete = async () => {
      try {
        await api.delete(`/courses/${id}`);
        onToast("Удалено");
        onNavigate("/courses");
      } catch (e) {
        onToast((e as Error).message);
      }
    };
    if (tg) {
      tg.showConfirm("Удалить курс?", (ok) => {
        if (ok) doDelete();
      });
    } else {
      if (confirm("Удалить курс?")) doDelete();
    }
  };

  const uploadImage =
    (type: string) => async (e: globalThis.Event) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      try {
        const data = await api.uploadFile<{ url: string }>(
          `/courses/${id}/upload-image?type=${type}`,
          file,
        );
        if (type === "desktop") setImageDesktop(data.url);
        else setImageMobile(data.url);
        onToast("Изображение загружено");
      } catch (err) {
        onToast((err as Error).message);
      }
    };

  if (loading) return <div className="loading">Загрузка...</div>;

  return (
    <div className="page">
      <h2>{isNew ? "Новый курс" : "Редактирование курса"}</h2>

      <div className="form">
        <label className="form-label">
          Название *
          <input
            className="form-input"
            type="text"
            value={form.title}
            onInput={update("title")}
            placeholder="Название курса"
          />
        </label>

        <label className="form-label">
          Описание *
          <textarea
            className="form-textarea"
            value={form.description}
            onInput={update("description")}
            rows={3}
            placeholder="Краткое описание"
          />
        </label>

        <label className="form-label">
          Подробное описание
          <textarea
            className="form-textarea"
            value={form.detailed_description}
            onInput={update("detailed_description")}
            rows={5}
            placeholder="Подробное описание (для раскрытия)"
          />
        </label>

        <label className="form-label">
          Расписание *
          <input
            className="form-input"
            type="text"
            value={form.schedule}
            onInput={update("schedule")}
            placeholder="Пн/Ср 19:00-20:30"
          />
        </label>

        <div className="form-row">
          <label className="form-label">
            Стоимость *
            <input
              className="form-input"
              type="number"
              value={form.cost}
              onInput={update("cost")}
              min={0}
              step={0.01}
            />
          </label>
          <label className="form-label">
            Валюта
            <select
              className="form-input"
              value={form.currency}
              onChange={update("currency")}
            >
              <option value="RUB">RUB</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
            </select>
          </label>
        </div>

        <label className="form-label">
          Порядок
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
              Изображение Desktop
              <input
                className="form-input"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={uploadImage("desktop")}
              />
            </label>
            {imageDesktop && (
              <img
                className="preview-image"
                src={imageDesktop}
                alt="Desktop"
              />
            )}

            <label className="form-label">
              Изображение Mobile
              <input
                className="form-input"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={uploadImage("mobile")}
              />
            </label>
            {imageMobile && (
              <img className="preview-image" src={imageMobile} alt="Mobile" />
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
