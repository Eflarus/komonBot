const tg = window.Telegram?.WebApp;

const BASE_URL = '';  // relative — same origin

function getInitData() {
    return tg?.initData || '';
}

async function request(method, path, { body, isFormData } = {}) {
    const headers = {
        'X-Telegram-Init-Data': getInitData(),
    };
    if (!isFormData) {
        headers['Content-Type'] = 'application/json';
    }

    const opts = { method, headers };
    if (body) {
        opts.body = isFormData ? body : JSON.stringify(body);
    }

    const res = await fetch(`${BASE_URL}/api${path}`, opts);

    if (res.status === 401) {
        // Session expired — close Mini App
        if (tg) {
            tg.showAlert('Сессия истекла. Откройте приложение заново.', () => {
                tg.close();
            });
        }
        throw new Error('Unauthorized');
    }

    if (res.status === 204) {
        return null;
    }

    if (!res.ok) {
        const err = await res.json().catch(() => ({ message: 'Request failed' }));
        throw new Error(err.message || `HTTP ${res.status}`);
    }

    return res.json();
}

export const api = {
    get: (path) => request('GET', path),
    post: (path, body) => request('POST', path, { body }),
    patch: (path, body) => request('PATCH', path, { body }),
    delete: (path) => request('DELETE', path),

    async uploadFile(path, file) {
        const formData = new FormData();
        formData.append('file', file);
        return request('POST', path, { body: formData, isFormData: true });
    },
};
