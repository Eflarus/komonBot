import { h } from 'https://esm.sh/preact@10.25.4';
import { useState, useEffect } from 'https://esm.sh/preact@10.25.4/hooks';
import htm from 'https://esm.sh/htm@3.1.1';
import { api } from '../services/api.js';

const html = htm.bind(h);
const tg = window.Telegram?.WebApp;

export function UserList({ onToast }) {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [newUser, setNewUser] = useState({ telegram_id: '', username: '', first_name: '' });

    const load = async () => {
        setLoading(true);
        try {
            const data = await api.get('/users');
            setUsers(data);
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    useEffect(() => { load(); }, []);

    const addUser = async () => {
        if (!newUser.telegram_id) {
            onToast('Укажите Telegram ID');
            return;
        }
        try {
            await api.post('/users', {
                telegram_id: parseInt(newUser.telegram_id),
                username: newUser.username || null,
                first_name: newUser.first_name || null,
            });
            onToast('Пользователь добавлен');
            setNewUser({ telegram_id: '', username: '', first_name: '' });
            setShowForm(false);
            load();
        } catch (e) { onToast(e.message); }
    };

    const removeUser = async (userId) => {
        const doRemove = async () => {
            try {
                await api.delete(`/users/${userId}`);
                onToast('Пользователь удалён');
                load();
            } catch (e) { onToast(e.message); }
        };
        if (tg) {
            tg.showConfirm('Удалить пользователя?', (ok) => { if (ok) doRemove(); });
        } else {
            if (confirm('Удалить пользователя?')) doRemove();
        }
    };

    return html`
        <div class="page">
            <div class="page-header">
                <h2>Пользователи</h2>
                <button class="btn btn-primary" onClick=${() => setShowForm(!showForm)}>
                    ${showForm ? 'Отмена' : '+ Добавить'}
                </button>
            </div>

            ${showForm ? html`
                <div class="form add-user-form">
                    <label class="form-label">
                        Telegram ID *
                        <input class="form-input" type="number"
                               value=${newUser.telegram_id}
                               onInput=${(e) => setNewUser(u => ({ ...u, telegram_id: e.target.value }))}
                               placeholder="123456789" />
                    </label>
                    <label class="form-label">
                        Username
                        <input class="form-input" type="text"
                               value=${newUser.username}
                               onInput=${(e) => setNewUser(u => ({ ...u, username: e.target.value }))}
                               placeholder="@username" />
                    </label>
                    <label class="form-label">
                        Имя
                        <input class="form-input" type="text"
                               value=${newUser.first_name}
                               onInput=${(e) => setNewUser(u => ({ ...u, first_name: e.target.value }))}
                               placeholder="Имя" />
                    </label>
                    <button class="btn btn-success" onClick=${addUser}>Добавить</button>
                </div>
            ` : null}

            ${loading ? html`<div class="loading">Загрузка...</div>` : html`
                <div class="card-list">
                    ${users.length === 0 ? html`<p class="empty">Нет пользователей</p>` : null}
                    ${users.map(u => html`
                        <div class="card user-card">
                            <div class="card-header">
                                <span class="card-title">
                                    ${u.first_name || ''} ${u.last_name || ''}
                                    ${u.username ? html` <span class="card-meta">@${u.username}</span>` : null}
                                </span>
                            </div>
                            <div class="card-meta">
                                ID: ${u.telegram_id}
                                · Добавлен: ${new Date(u.created_at).toLocaleDateString('ru')}
                            </div>
                            <button class="btn btn-danger btn-sm"
                                    onClick=${(e) => { e.stopPropagation(); removeUser(u.id); }}>
                                Удалить
                            </button>
                        </div>
                    `)}
                </div>
            `}
        </div>
    `;
}
