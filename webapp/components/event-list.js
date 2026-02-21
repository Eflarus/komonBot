import { h } from 'https://esm.sh/preact@10.25.4';
import { useState, useEffect } from 'https://esm.sh/preact@10.25.4/hooks';
import htm from 'https://esm.sh/htm@3.1.1';
import { api } from '../services/api.js';

const html = htm.bind(h);

const STATUS_LABELS = {
    draft: 'Черновик',
    published: 'Опубликовано',
    cancelled: 'Отменено',
    archived: 'Архив',
};

const STATUS_TABS = [null, 'draft', 'published', 'cancelled', 'archived'];
const TAB_LABELS = ['Все', 'Черновики', 'Опубликованные', 'Отменённые', 'Архив'];

export function EventList({ onNavigate }) {
    const [events, setEvents] = useState([]);
    const [total, setTotal] = useState(0);
    const [tab, setTab] = useState(0);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);

    const load = async () => {
        setLoading(true);
        try {
            const status = STATUS_TABS[tab];
            let path = `/events?limit=50`;
            if (status) path += `&status=${status}`;
            if (search) path += `&search=${encodeURIComponent(search)}`;
            const data = await api.get(path);
            setEvents(data.items);
            setTotal(data.total);
        } catch (e) {
            console.error(e);
        }
        setLoading(false);
    };

    useEffect(() => { load(); }, [tab, search]);

    return html`
        <div class="page">
            <div class="page-header">
                <h2>Мероприятия</h2>
                <button class="btn btn-primary" onClick=${() => onNavigate('/events/new')}>
                    + Создать
                </button>
            </div>

            <div class="tabs">
                ${TAB_LABELS.map((label, i) => html`
                    <button class="tab ${tab === i ? 'active' : ''}"
                            onClick=${() => setTab(i)}>
                        ${label}
                    </button>
                `)}
            </div>

            <input class="search-input" type="text" placeholder="Поиск..."
                   value=${search}
                   onInput=${(e) => setSearch(e.target.value)} />

            ${loading ? html`<div class="loading">Загрузка...</div>` : html`
                <div class="card-list">
                    ${events.length === 0 ? html`<p class="empty">Нет мероприятий</p>` : null}
                    ${events.map(event => html`
                        <div class="card" onClick=${() => onNavigate('/events/' + event.id)}>
                            <div class="card-header">
                                <span class="card-title">${event.title}</span>
                                <span class="status-badge status-${event.status}">
                                    ${STATUS_LABELS[event.status]}
                                </span>
                            </div>
                            <div class="card-meta">
                                ${event.event_date || ''} ${event.event_time || ''}
                                ${event.location ? ` · ${event.location}` : ''}
                            </div>
                        </div>
                    `)}
                </div>
            `}
        </div>
    `;
}
