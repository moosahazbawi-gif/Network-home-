const state = {
  token: localStorage.getItem('cloudbell_token') || '',
  me: null,
};

const el = (id) => document.getElementById(id);
const authMessage = el('authMessage');
const bootstrapForm = el('bootstrapForm');
const loginForm = el('loginForm');
const transferForm = el('transferForm');
const appPanel = el('appPanel');
const logoutBtn = el('logoutBtn');
const meBox = el('meBox');
const transfersBox = el('transfers');
const refreshBtn = el('refreshBtn');

function setMessage(text, kind = 'info') {
  authMessage.textContent = text;
  authMessage.style.color = kind === 'error' ? '#b42318' : '#5f6b7a';
}

function authHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  return headers;
}

async function api(path, options = {}) {
  const resp = await fetch(`/api${path}`, {
    ...options,
    headers: {
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  const contentType = resp.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await resp.json() : await resp.text();
  if (!resp.ok) {
    const msg = data && data.detail ? data.detail : (typeof data === 'string' ? data : 'فشل الطلب');
    const err = new Error(msg);
    err.status = resp.status;
    throw err;
  }
  return data;
}

function renderMe() {
  meBox.textContent = JSON.stringify(state.me, null, 2);
}

function statusClass(status) {
  return ['completed', 'failed', 'canceled'].includes(status) ? status : '';
}

async function refreshTransfers() {
  const items = await api('/transfers');
  transfersBox.innerHTML = '';
  if (!items.length) {
    transfersBox.innerHTML = '<p class="meta">لا توجد طلبات بعد.</p>';
    return;
  }
  const wrap = document.createElement('div');
  wrap.className = 'table';
  for (const item of items) {
    const row = document.createElement('section');
    row.className = 'row';
    row.innerHTML = `
      <div class="row-head">
        <strong>#${item.id} ${item.safe_filename || item.source_url}</strong>
        <span class="status ${statusClass(item.status)}">${item.status}</span>
      </div>
      <div class="meta">${item.source_url}</div>
      <div class="meta">${item.byte_size ? `${item.byte_size} بايت` : 'لم يكتمل'}</div>
      <div class="actions"></div>
    `;
    const actions = row.querySelector('.actions');
    const view = document.createElement('button');
    view.className = 'ghost';
    view.textContent = 'تفاصيل';
    view.onclick = async () => {
      const detail = await api(`/transfers/${item.id}`);
      alert(JSON.stringify(detail, null, 2));
    };
    actions.appendChild(view);
    if (item.status === 'completed') {
      const dl = document.createElement('a');
      dl.className = 'button-link';
      dl.href = `/api/transfers/${item.id}/file`;
      dl.textContent = 'تحميل الملف';
      dl.style.cssText = 'display:inline-block;padding:10px 14px;border-radius:6px;background:#1f6feb;color:#fff;text-decoration:none;';
      actions.appendChild(dl);
    }
    if (item.status === 'queued' || item.status === 'running') {
      const cancel = document.createElement('button');
      cancel.className = 'ghost';
      cancel.textContent = 'إلغاء';
      cancel.onclick = async () => {
        await api(`/transfers/${item.id}/cancel`, { method: 'POST' });
        await loadDashboard();
      };
      actions.appendChild(cancel);
    }
    wrap.appendChild(row);
  }
  transfersBox.appendChild(wrap);
}

async function loadDashboard() {
  state.me = await api('/auth/me');
  renderMe();
  appPanel.classList.remove('hidden');
  logoutBtn.classList.remove('hidden');
  bootstrapForm.classList.add('hidden');
  setMessage('');
  await refreshTransfers();
}

loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(loginForm);
  try {
    const data = await api('/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        email: form.get('email'),
        password: form.get('password'),
      }),
    });
    state.token = data.access_token;
    localStorage.setItem('cloudbell_token', state.token);
    await loadDashboard();
  } catch (err) {
    if (err.status === 404 || err.status === 400) {
      bootstrapForm.classList.remove('hidden');
    }
    setMessage(err.message, 'error');
  }
});

bootstrapForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(bootstrapForm);
  try {
    await api('/auth/bootstrap-admin', {
      method: 'POST',
      body: JSON.stringify({
        email: form.get('email'),
        password: form.get('password'),
      }),
    });
    setMessage('تم إنشاء المسؤول. سجل الدخول الآن.');
  } catch (err) {
    setMessage(err.message, 'error');
  }
});

transferForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(transferForm);
  try {
    await api('/transfers', {
      method: 'POST',
      body: JSON.stringify({ url: form.get('url') }),
    });
    transferForm.reset();
    await refreshTransfers();
  } catch (err) {
    alert(err.message);
  }
});

refreshBtn.addEventListener('click', refreshTransfers);
logoutBtn.addEventListener('click', () => {
  state.token = '';
  state.me = null;
  localStorage.removeItem('cloudbell_token');
  appPanel.classList.add('hidden');
  logoutBtn.classList.add('hidden');
  bootstrapForm.classList.add('hidden');
  meBox.textContent = '';
  transfersBox.innerHTML = '';
  setMessage('تم تسجيل الخروج.');
});

(async () => {
  if (!state.token) {
    bootstrapForm.classList.remove('hidden');
    return;
  }
  try {
    await loadDashboard();
  } catch (err) {
    localStorage.removeItem('cloudbell_token');
    state.token = '';
    setMessage('انتهت الجلسة. سجل الدخول من جديد.', 'error');
    bootstrapForm.classList.remove('hidden');
  }
})();
