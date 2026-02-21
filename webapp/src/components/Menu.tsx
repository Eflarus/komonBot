function navigate(path: string) {
  window.location.hash = path;
}

export function Menu() {
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
    </div>
  );
}
