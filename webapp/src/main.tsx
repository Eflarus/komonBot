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
import { api } from "./services/api";

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

type AuthState = "loading" | "allowed" | "denied" | "no_telegram" | "error";

function App() {
  const [route, setRoute] = useState<Route>(parseRoute());
  const [toast, setToast] = useState<string | null>(null);
  const [auth, setAuth] = useState<AuthState>(
    tg?.initData ? "loading" : "no_telegram",
  );

  useEffect(() => {
    if (auth !== "loading") return;
    api
      .get("/users/me")
      .then(() => setAuth("allowed"))
      .catch((err) => {
        if (err.message === "Forbidden") setAuth("denied");
        else if (err.message === "Unauthorized") setAuth("denied");
        else setAuth("error");
      });
  }, [auth]);

  // Signal Telegram that we're ready once auth resolves
  useEffect(() => {
    if (auth === "loading") return;
    if (tg) tg.ready();
  }, [auth]);

  useEffect(() => {
    if (auth !== "allowed") return;
    setRoute(parseRoute());
    const onHash = () => setRoute(parseRoute());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, [auth]);

  // Telegram Back button
  useEffect(() => {
    if (auth !== "allowed" || !tg) return;
    if (route.path === "/" || route.path === "") {
      tg.BackButton.hide();
    } else {
      tg.BackButton.show();
      const handler = () => goBack(route.parts);
      tg.BackButton.onClick(handler);
      return () => tg.BackButton.offClick(handler);
    }
  }, [auth, route.path]);

  if (auth === "no_telegram") {
    return (
      <div className="app">
        <div className="auth-message">
          <h2>Доступ запрещён</h2>
          <p>Откройте приложение через Telegram-бот.</p>
        </div>
      </div>
    );
  }

  if (auth === "loading") {
    return (
      <div className="app">
        <div className="auth-message">
          <p>Загрузка...</p>
        </div>
      </div>
    );
  }

  if (auth === "error") {
    return (
      <div className="app">
        <div className="auth-message">
          <h2>Ошибка соединения</h2>
          <p>Не удалось проверить доступ.</p>
          <button className="btn" onClick={() => setAuth("loading")}>
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  if (auth === "denied") {
    return (
      <div className="app">
        <div className="auth-message">
          <h2>Доступ запрещён</h2>
          <p>У вас нет доступа к этому приложению.</p>
        </div>
      </div>
    );
  }

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

// Init Telegram WebApp (ready() is deferred until auth resolves)
if (tg) {
  tg.expand();
}

render(<App />, document.getElementById("app")!);
