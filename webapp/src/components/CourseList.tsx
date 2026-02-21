import { useState, useEffect } from "preact/hooks";
import { api } from "@/services/api";
import type { Course, EntityStatus, PaginatedResponse } from "@/types";

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

interface CourseListProps {
  onNavigate: (path: string) => void;
}

export function CourseList({ onNavigate }: CourseListProps) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [_total, setTotal] = useState(0);
  const [tab, setTab] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const status = STATUS_TABS[tab];
      let path = `/courses?limit=50`;
      if (status) path += `&status=${status}`;
      if (search) path += `&search=${encodeURIComponent(search)}`;
      const data = await api.get<PaginatedResponse<Course>>(path);
      setCourses(data.items);
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
        <h2>Курсы</h2>
        <button
          className="btn btn-primary"
          onClick={() => onNavigate("/courses/new")}
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
          {courses.length === 0 && <p className="empty">Нет курсов</p>}
          {courses.map((course) => (
            <div
              key={course.id}
              className="card"
              onClick={() => onNavigate("/courses/" + course.id)}
            >
              <div className="card-header">
                <span className="card-title">{course.title}</span>
                <span className={`status-badge status-${course.status}`}>
                  {STATUS_LABELS[course.status]}
                </span>
              </div>
              <div className="card-meta">
                {course.schedule} · {course.cost} {course.currency}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
