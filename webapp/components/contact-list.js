import { h } from 'https://esm.sh/preact@10.25.4';
import { useState, useEffect } from 'https://esm.sh/preact@10.25.4/hooks';
import htm from 'https://esm.sh/htm@3.1.1';
import { api } from '../services/api.js';

const html = htm.bind(h);

export function ContactList({ onToast }) {
    const [contacts, setContacts] = useState([]);
    const [tab, setTab] = useState(0); // 0=unprocessed, 1=processed, 2=all
    const [loading, setLoading] = useState(true);

    const load = async () => {
        setLoading(true);
        try {
            let path = '/contacts?limit=50';
            if (tab === 0) path += '&is_processed=false';
            else if (tab === 1) path += '&is_processed=true';
            const data = await api.get(path);
            setContacts(data.items);
        } catch (e) {
            console.error(e);
        }
        setLoading(false);
    };

    useEffect(() => { load(); }, [tab]);

    const markProcessed = async (id) => {
        try {
            await api.patch(`/contacts/${id}/process`);
            onToast('Заявка обработана');
            load();
        } catch (e) { onToast(e.message); }
    };

    return html`
        <div class="page">
            <h2>Заявки</h2>

            <div class="tabs">
                <button class="tab ${tab === 0 ? 'active' : ''}" onClick=${() => setTab(0)}>
                    Новые
                </button>
                <button class="tab ${tab === 1 ? 'active' : ''}" onClick=${() => setTab(1)}>
                    Обработанные
                </button>
                <button class="tab ${tab === 2 ? 'active' : ''}" onClick=${() => setTab(2)}>
                    Все
                </button>
            </div>

            ${loading ? html`<div class="loading">Загрузка...</div>` : html`
                <div class="card-list">
                    ${contacts.length === 0 ? html`<p class="empty">Нет заявок</p>` : null}
                    ${contacts.map(c => html`
                        <div class="card contact-card">
                            <div class="card-header">
                                <span class="card-title">${c.name}</span>
                                <span class="status-badge ${c.is_processed ? 'status-archived' : 'status-draft'}">
                                    ${c.is_processed ? 'Обработана' : 'Новая'}
                                </span>
                            </div>
                            <div class="card-meta">
                                <div>Тел: ${c.phone}</div>
                                ${c.email ? html`<div>Email: ${c.email}</div>` : null}
                                ${c.source ? html`<div>Источник: ${c.source}</div>` : null}
                            </div>
                            <div class="card-body">${c.message}</div>
                            <div class="card-meta">
                                ${new Date(c.created_at).toLocaleString('ru')}
                            </div>
                            ${!c.is_processed ? html`
                                <button class="btn btn-success btn-sm"
                                        onClick=${(e) => { e.stopPropagation(); markProcessed(c.id); }}>
                                    Обработано
                                </button>
                            ` : null}
                        </div>
                    `)}
                </div>
            `}
        </div>
    `;
}
