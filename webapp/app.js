import { h, render } from 'https://esm.sh/preact@10.25.4';
import { useState, useEffect } from 'https://esm.sh/preact@10.25.4/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

import { EventList } from './components/event-list.js';
import { EventForm } from './components/event-form.js';
import { CourseList } from './components/course-list.js';
import { CourseForm } from './components/course-form.js';
import { ContactList } from './components/contact-list.js';
import { UserList } from './components/user-list.js';

const html = htm.bind(h);

const tg = window.Telegram?.WebApp;

function parseRoute() {
    const hash = window.location.hash.slice(1) || '/';
    const parts = hash.split('/').filter(Boolean);
    return { path: hash, parts };
}

function navigate(path) {
    window.location.hash = path;
}

function Menu() {
    return html`
        <div class="menu">
            <h1 class="menu-title">KomonBot</h1>
            <div class="menu-grid">
                <button class="menu-btn" onClick=${() => navigate('/events')}>
                    <span class="menu-btn-icon">📅</span>
                    <span>Мероприятия</span>
                </button>
                <button class="menu-btn" onClick=${() => navigate('/courses')}>
                    <span class="menu-btn-icon">📚</span>
                    <span>Курсы</span>
                </button>
                <button class="menu-btn" onClick=${() => navigate('/contacts')}>
                    <span class="menu-btn-icon">📩</span>
                    <span>Заявки</span>
                </button>
                <button class="menu-btn" onClick=${() => navigate('/users')}>
                    <span class="menu-btn-icon">👥</span>
                    <span>Пользователи</span>
                </button>
            </div>
        </div>
    `;
}

function Toast({ message, onClose }) {
    useEffect(() => {
        if (message) {
            const timer = setTimeout(onClose, 3000);
            return () => clearTimeout(timer);
        }
    }, [message]);

    if (!message) return null;
    return html`<div class="toast">${message}</div>`;
}

function App() {
    const [route, setRoute] = useState(parseRoute());
    const [toast, setToast] = useState(null);

    useEffect(() => {
        const onHash = () => setRoute(parseRoute());
        window.addEventListener('hashchange', onHash);
        return () => window.removeEventListener('hashchange', onHash);
    }, []);

    // Back button handling
    useEffect(() => {
        if (!tg) return;
        if (route.path === '/' || route.path === '') {
            tg.BackButton.hide();
        } else {
            tg.BackButton.show();
            const handler = () => {
                const { parts } = route;
                if (parts.length <= 1) {
                    navigate('/');
                } else if (parts.length === 2 && (parts[1] === 'new' || !isNaN(parts[1]))) {
                    navigate('/' + parts[0]);
                } else {
                    navigate('/' + parts.slice(0, -1).join('/'));
                }
            };
            tg.BackButton.onClick(handler);
            return () => tg.BackButton.offClick(handler);
        }
    }, [route.path]);

    const showToast = (msg) => setToast(msg);
    const { parts } = route;

    let content;
    if (parts[0] === 'events') {
        if (parts[1] === 'new') {
            content = html`<${EventForm} onNavigate=${navigate} onToast=${showToast} />`;
        } else if (parts[1]) {
            content = html`<${EventForm} id=${parts[1]} onNavigate=${navigate} onToast=${showToast} />`;
        } else {
            content = html`<${EventList} onNavigate=${navigate} />`;
        }
    } else if (parts[0] === 'courses') {
        if (parts[1] === 'new') {
            content = html`<${CourseForm} onNavigate=${navigate} onToast=${showToast} />`;
        } else if (parts[1]) {
            content = html`<${CourseForm} id=${parts[1]} onNavigate=${navigate} onToast=${showToast} />`;
        } else {
            content = html`<${CourseList} onNavigate=${navigate} />`;
        }
    } else if (parts[0] === 'contacts') {
        content = html`<${ContactList} onToast=${showToast} />`;
    } else if (parts[0] === 'users') {
        content = html`<${UserList} onToast=${showToast} />`;
    } else {
        content = html`<${Menu} />`;
    }

    return html`
        <div class="app">
            ${content}
            <${Toast} message=${toast} onClose=${() => setToast(null)} />
        </div>
    `;
}

// Init Telegram WebApp
if (tg) {
    tg.ready();
    tg.expand();
}

render(html`<${App} />`, document.getElementById('app'));

export { html, navigate };
