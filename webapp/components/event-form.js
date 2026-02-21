import { h } from 'https://esm.sh/preact@10.25.4';
import { useState, useEffect } from 'https://esm.sh/preact@10.25.4/hooks';
import htm from 'https://esm.sh/htm@3.1.1';
import { api } from '../services/api.js';

const html = htm.bind(h);
const tg = window.Telegram?.WebApp;

const DRAFT_KEY = 'komonbot_event_draft';

function loadDraft() {
    try {
        return JSON.parse(localStorage.getItem(DRAFT_KEY)) || {};
    } catch { return {}; }
}
function saveDraft(data) {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(data));
}
function clearDraft() {
    localStorage.removeItem(DRAFT_KEY);
}

export function EventForm({ id, onNavigate, onToast }) {
    const isNew = !id;
    const [form, setForm] = useState({
        title: '', description: '', location: '',
        event_date: '', event_time: '', ticket_link: '', order: 0,
    });
    const [status, setStatus] = useState('draft');
    const [coverImage, setCoverImage] = useState(null);
    const [loading, setLoading] = useState(!isNew);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (isNew) {
            const draft = loadDraft();
            if (draft.title) setForm(f => ({ ...f, ...draft }));
        } else {
            api.get(`/events/${id}`).then(data => {
                setForm({
                    title: data.title || '',
                    description: data.description || '',
                    location: data.location || '',
                    event_date: data.event_date || '',
                    event_time: data.event_time ? data.event_time.slice(0, 5) : '',
                    ticket_link: data.ticket_link || '',
                    order: data.order || 0,
                });
                setStatus(data.status);
                setCoverImage(data.cover_image);
                setLoading(false);
            }).catch(e => { onToast(e.message); setLoading(false); });
        }
    }, [id]);

    // Auto-save draft for new events
    useEffect(() => {
        if (isNew) saveDraft(form);
    }, [form, isNew]);

    const update = (field) => (e) => {
        setForm(f => ({ ...f, [field]: e.target.value }));
    };

    const save = async () => {
        setSaving(true);
        try {
            if (isNew) {
                const data = await api.post('/events', form);
                clearDraft();
                onToast('Мероприятие создано');
                onNavigate(`/events/${data.id}`);
            } else {
                await api.patch(`/events/${id}`, form);
                onToast('Сохранено');
            }
        } catch (e) { onToast(e.message); }
        setSaving(false);
    };

    const publish = async () => {
        try {
            await api.post(`/events/${id}/publish`);
            setStatus('published');
            onToast('Опубликовано');
        } catch (e) { onToast(e.message); }
    };

    const unpublish = async () => {
        try {
            await api.post(`/events/${id}/unpublish`);
            setStatus('draft');
            onToast('Снято с публикации');
        } catch (e) { onToast(e.message); }
    };

    const cancel = async () => {
        try {
            await api.post(`/events/${id}/cancel`);
            setStatus('cancelled');
            onToast('Отменено');
        } catch (e) { onToast(e.message); }
    };

    const remove = async () => {
        if (tg) {
            tg.showConfirm('Удалить мероприятие?', async (ok) => {
                if (!ok) return;
                try {
                    await api.delete(`/events/${id}`);
                    onToast('Удалено');
                    onNavigate('/events');
                } catch (e) { onToast(e.message); }
            });
        } else {
            if (!confirm('Удалить мероприятие?')) return;
            try {
                await api.delete(`/events/${id}`);
                onToast('Удалено');
                onNavigate('/events');
            } catch (e) { onToast(e.message); }
        }
    };

    const uploadImage = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        try {
            const data = await api.uploadFile(`/events/${id}/upload-image`, file);
            setCoverImage(data.url);
            onToast('Изображение загружено');
        } catch (err) { onToast(err.message); }
    };

    if (loading) return html`<div class="loading">Загрузка...</div>`;

    return html`
        <div class="page">
            <h2>${isNew ? 'Новое мероприятие' : 'Редактирование'}</h2>

            <div class="form">
                <label class="form-label">
                    Название *
                    <input class="form-input" type="text" value=${form.title}
                           onInput=${update('title')} placeholder="Название" />
                </label>

                <label class="form-label">
                    Описание
                    <textarea class="form-textarea" value=${form.description}
                              onInput=${update('description')} rows="3"
                              placeholder="Описание (внутренние заметки)" />
                </label>

                <label class="form-label">
                    Место *
                    <input class="form-input" type="text" value=${form.location}
                           onInput=${update('location')} placeholder="Место проведения" />
                </label>

                <div class="form-row">
                    <label class="form-label">
                        Дата *
                        <input class="form-input" type="date" value=${form.event_date}
                               onInput=${update('event_date')} />
                    </label>
                    <label class="form-label">
                        Время *
                        <input class="form-input" type="time" value=${form.event_time}
                               onInput=${update('event_time')} />
                    </label>
                </div>

                <label class="form-label">
                    Ссылка на билеты
                    <input class="form-input" type="url" value=${form.ticket_link}
                           onInput=${update('ticket_link')} placeholder="https://..." />
                </label>

                <label class="form-label">
                    Порядок отображения
                    <input class="form-input" type="number" value=${form.order}
                           onInput=${update('order')} min="0" />
                </label>

                ${!isNew ? html`
                    <label class="form-label">
                        Обложка (516x516)
                        <input class="form-input" type="file" accept="image/jpeg,image/png,image/webp"
                               onChange=${uploadImage} />
                    </label>
                    ${coverImage ? html`
                        <img class="preview-image" src=${coverImage} alt="Cover" />
                    ` : null}
                ` : null}

                <div class="form-actions">
                    <button class="btn btn-primary" onClick=${save} disabled=${saving}>
                        ${saving ? 'Сохранение...' : 'Сохранить'}
                    </button>

                    ${!isNew ? html`
                        ${status === 'draft' ? html`
                            <button class="btn btn-success" onClick=${publish}>Опубликовать</button>
                        ` : null}
                        ${status === 'published' ? html`
                            <button class="btn btn-warning" onClick=${unpublish}>Снять</button>
                            <button class="btn btn-danger" onClick=${cancel}>Отменить</button>
                        ` : null}
                        ${status !== 'published' ? html`
                            <button class="btn btn-danger" onClick=${remove}>Удалить</button>
                        ` : null}
                    ` : null}
                </div>
            </div>
        </div>
    `;
}
