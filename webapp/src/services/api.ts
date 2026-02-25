const tg = window.Telegram?.WebApp;

function getInitData(): string {
  return tg?.initData || "";
}

function getApiBase(): string {
  // Derive API prefix from current page URL
  // e.g. /bot179654/webapp/ → /bot179654/api
  const path = window.location.pathname;
  const idx = path.indexOf("/webapp");
  return (idx > 0 ? path.substring(0, idx) : "") + "/api";
}

interface RequestOptions {
  body?: unknown;
  isFormData?: boolean;
}

async function request<T>(
  method: string,
  path: string,
  { body, isFormData }: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "X-Telegram-Init-Data": getInitData(),
  };
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  const opts: RequestInit = { method, headers };
  if (body) {
    opts.body = isFormData ? (body as FormData) : JSON.stringify(body);
  }

  const res = await fetch(`${getApiBase()}${path}`, opts);

  if (res.status === 401) {
    if (tg) {
      tg.showAlert("Сессия истекла. Откройте приложение заново.", () => {
        tg.close();
      });
    }
    throw new Error("Unauthorized");
  }

  if (res.status === 403) {
    throw new Error("Forbidden");
  }

  if (res.status === 204) {
    return null as T;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: "Request failed" }));
    throw new Error(err.message || `HTTP ${res.status}`);
  }

  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) =>
    request<T>("POST", path, { body }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>("PATCH", path, { body }),
  delete: <T>(path: string) => request<T>("DELETE", path),

  async uploadFile<T>(path: string, file: File): Promise<T> {
    const formData = new FormData();
    formData.append("file", file);
    return request<T>("POST", path, { body: formData, isFormData: true });
  },
};
