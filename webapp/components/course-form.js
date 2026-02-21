import { h } from 'https://esm.sh/preact@10.25.4';
import { useState, useEffect } from 'https://esm.sh/preact@10.25.4/hooks';
import htm from 'https://esm.sh/htm@3.1.1';
import { api } from '../services/api.js';

const html = htm.bind(h);
const tg = window.Telegram?.WebApp;

const DRAFT_KEY = 'komonbot_course_draft';

function loadDraft() {
    try { return JSON.parse(localStorage.getItem(DRAFT_KEY)) || {}; }
    catch { return {}; }
}
function saveDraft(data) { localStorage.setItem(DRAFT_KEY, JSON.stringify(data)); }
function clearDraft() { localStorage.removeItem(DRAFT_KEY); }

export function CourseForm({ id, onNavigate, onToast }) {
    const isNew = !id;
    const [form, setForm] = useState({
        title: '', description: '', detailed_description: '',
        schedule: '', cost: '0', currency: 'RUB', order: 0,
    });
    const [status, setStatus] = useState('draft');
    const [imageDesktop, setImageDesktop] = useState(null);
    const [imageMobile, setImageMobile] = useState(null);
    const [loading, setLoading] = useState(!isNew);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (isNew) {
            const draft = loadDraft();
            if (draft.title) setForm(f => ({ ...f, ...draft }));
        } else {
            api.get(`/courses/${id}`).then(data => {
                setForm({
                    title: data.title || '',
                    description: data.description || '',
                    detailed_description: data.detailed_description || '',
                    schedule: data.schedule || '',
                    cost: String(data.cost || 0),
                    currency: data.currency || 'RUB',
                    order: data.order || 0,
                });
                setStatus(data.status);
                setImageDesktop(data.image_desktop);
                setImageMobile(data.image_mobile);
                setLoading(false);
            }).catch(e => { onToast(e.message); setLoading(false); });
        }
    }, [id]);

    useEffect(() => {
        if (isNew) saveDraft(form);
    }, [form, isNew]);

    const update = (field) => (e) => {
        setForm(f => ({ ...f, [field]: e.target.value }));
    };

    const save = async () => {
        setSaving(true);
        try {
            const payload = { ...form, cost: parseFloat(form.cost) || 0 };
            if (isNew) {
                const data = await api.post('/courses', payload);
                clearDraft();
                onToast('Курс создан');
                onNavigate(`/courses/${data.id}`);
            } else {
                await api.patch(`/courses/${id}`, payload);
                onToast('Сохранено');
            }
        } catch (e) { onToast(e.message); }
        setSaving(false);
    };

    const publish = async () => {
        try {
            await api.post(`/courses/${id}/publish`);
            setStatus('published');
            onToast('Опубликовано');
        } catch (e) { onToast(e.message); }
    };

    const unpublish = async () => {
        try {
            await api.post(`/courses/${id}/unpublish`);
            setStatus('draft');
            onToast('Снято с публикации');
        } catch (e) { onToast(e.message); }
    };

    const cancel = async () => {
        try {
            await api.post(`/courses/${id}/cancel`);
            setStatus('cancelled');
            onToast('Отменено');
        } catch (e) { onToast(e.message); }
    };

    const remove = async () => {
        const doDelete = async () => {
            try {
                await api.delete(`/courses/${id}`);
                onToast('Удалено');
                onNavigate('/courses');
            } catch (e) { onToast(e.message); }
        };
        if (tg) {
            tg.showConfirm('Удалить курс?', (ok) => { if (ok) doDelete(); });
        } else {
            if (confirm('Удалить курс?')) doDelete();
        }
    };

    const uploadImage = (type) => async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        try {
            const data = await api.uploadFile(`/courses/${id}/upload-image?type=${type}`, file);
            if (type === 'desktop') setImageDesktop(data.url);
            else setImageMobile(data.url);
            onToast('Изображение загружено');
        } catch (err) { onToast(err.message); }
    };

    if (loading) return html`<div class="loading">Загрузка...</div>`;

    return html`
        <div class="page">
            <h2>${isNew ? 'Новый курс' : 'Редактирование курса'}</h2>

            <div class="form">
                <label class="form-label">
                    Название *
                    <input class="form-input" type="text" value=${form.title}
                           onInput=${update('title')} placeholder="Название курса" />
                </label>

                <label class="form-label">
                    Описание *
                    <textarea class="form-textarea" value=${form.description}
                              onInput=${update('description')} rows="3"
                              placeholder="Краткое описание" />
                </label>

                <label class="form-label">
                    Подробное описание
                    <textarea class="form-textarea" value=${form.detailed_description}
                              onInput=${update('detailed_description')} rows="5"
                              placeholder="Подробное описание (для раскрытия)" />
                </label>

                <label class="form-label">
                    Расписание *
                    <input class="form-input" type="text" value=${form.schedule}
                           onInput=${update('schedule')} placeholder="Пн/Ср 19:00-20:30" />
                </label>

                <div class="form-row">
                    <label class="form-label">
                        Стоимость *
                        <input class="form-input" type="number" value=${form.cost}
                               onInput=${update('cost')} min="0" step="0.01" />
                    </label>
                    <label class="form-label">
                        Валюта
                        <select class="form-input" value=${form.currency}
                                onChange=${update('currency')}>
                            <option value="RUB">RUB</option>
                            <option value="USD">USD</option>
                            <option value="EUR">EUR</option>
                        </select>
                    </label>
                </div>

                <label class="form-label">
                    Порядок
                    <input class="form-input" type="number" value=${form.order}
                           onInput=${update('order')} min="0" />
                </label>

                ${!isNew ? html`
                    <label class="form-label">
                        Изображение Desktop
                        <input class="form-input" type="file" accept="image/jpeg,image/png,image/webp"
                               onChange=${uploadImage('desktop')} />
                    </label>
                    ${imageDesktop ? html`<img class="preview-image" src=${imageDesktop} alt="Desktop" />` : null}

                    <label class="form-label">
                        Изображение Mobile
                        <input class="form-input" type="file" accept="image/jpeg,image/png,image/webp"
                               onChange=${uploadImage('mobile')} />
                    </label>
                    ${imageMobile ? html`<img class="preview-image" src=${imageMobile} alt="Mobile" />` : null}
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
