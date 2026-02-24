import { render } from "preact";
import { useState, useEffect } from "preact/hooks";
import "../styles/app.css";

import { EventList } from "./components/EventList";
import { EventForm } from "./components/EventForm";
import { CourseList } from "./components/CourseList";
import { CourseForm } from "./components/CourseForm";
import { ContactList } from "./components/ContactList";
import { UserList } from "./components/UserList";
import { Menu } from "./components/Menu";
import { Toast } from "./components/Toast";

const tg = window.Telegram?.WebApp;

interface Route {
  path: string;
  parts: string[];
}

function parseRoute(): Route {
  const hash = window.location.hash.slice(1) || "/";
  const parts = hash.split("/").filter(Boolean);
  return { path: hash, parts };
}

function navigate(path: string) {
  window.location.hash = path;
}

function goBack(parts: string[]) {
  if (parts.length <= 1) {
    navigate("/");
  } else if (
    parts.length === 2 &&
    (parts[1] === "new" || !isNaN(Number(parts[1])))
  ) {
    navigate("/" + parts[0]);
  } else {
    navigate("/" + parts.slice(0, -1).join("/"));
  }
}

function App() {
  const [route, setRoute] = useState<Route>(parseRoute());
  const [toast, setToast] = useState<string | null>(null);

  // Auth: require Telegram environment
  if (!tg?.initData) {
    return (
      <div className="app">
        <div className="page" style={{ textAlign: "center", paddingTop: "3rem" }}>
          <h2>Доступ запрещён</h2>
          <p>Откройте приложение через Telegram-бот.</p>
        </div>
      </div>
    );
  }

  useEffect(() => {
    const onHash = () => setRoute(parseRoute());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  // Telegram Back button
  useEffect(() => {
    if (!tg) return;
    if (route.path === "/" || route.path === "") {
      tg.BackButton.hide();
    } else {
      tg.BackButton.show();
      const handler = () => goBack(route.parts);
      tg.BackButton.onClick(handler);
      return () => tg.BackButton.offClick(handler);
    }
  }, [route.path]);

  const showToast = (msg: string) => setToast(msg);
  const { parts } = route;
  const isSubPage = parts.length > 0;

  let content;
  if (parts[0] === "events") {
    if (parts[1] === "new") {
      content = (
        <EventForm onNavigate={navigate} onToast={showToast} />
      );
    } else if (parts[1]) {
      content = (
        <EventForm id={parts[1]} onNavigate={navigate} onToast={showToast} />
      );
    } else {
      content = <EventList onNavigate={navigate} />;
    }
  } else if (parts[0] === "courses") {
    if (parts[1] === "new") {
      content = (
        <CourseForm onNavigate={navigate} onToast={showToast} />
      );
    } else if (parts[1]) {
      content = (
        <CourseForm id={parts[1]} onNavigate={navigate} onToast={showToast} />
      );
    } else {
      content = <CourseList onNavigate={navigate} />;
    }
  } else if (parts[0] === "contacts") {
    content = <ContactList onToast={showToast} />;
  } else if (parts[0] === "users") {
    content = <UserList onToast={showToast} />;
  } else {
    content = <Menu />;
  }

  return (
    <div className="app">
      {isSubPage && (
        <button className="back-btn" onClick={() => goBack(parts)}>
          ← Назад
        </button>
      )}
      {content}
      <Toast message={toast} onClose={() => setToast(null)} />
    </div>
  );
}

// Init Telegram WebApp
if (tg) {
  tg.ready();
  tg.expand();
}

render(<App />, document.getElementById("app")!);
