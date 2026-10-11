const API_BASE = window.location.pathname.startsWith('/cloudbell-pro/') ? '/cloudbell-pro/api' : '/api';
const state = { token: localStorage.getItem('cloudbell_token') || '', me: null };
const el = (id) => document.getElementById(id);
const authMessage = el('authMessage'), bootstrapForm = el('bootstrapForm'), loginForm = el('loginForm');
const transferForm = el('transferForm'), appPanel = el('appPanel'), logoutBtn = el('logoutBtn');
const meBox = el('meBox'), transfersBox = el('transfers'), refreshBtn = el('refreshBtn');
const uploadForm = el('uploadForm'), fileInput = el('fileInput'), uploadsBox = el('uploads'); // اصلاح اضافه شده
const submitBtn = transferForm.querySelector('button[type="submit"]');

function setMessage(text, kind = 'info') { authMessage.textContent = text; authMessage.className = `message ${kind}`; }
function authHeaders() { const h = { 'Content-Type': 'application/json' }; if (state.token) h.Authorization = 'Bearer ' + state.token; return h; }

async function api(path, options = {}) {
  const headers = { ...authHeaders(), ...(options.headers || {}) };
  if (options.body instanceof FormData) delete headers['Content-Type'];
  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const ct = resp.headers.get('content-type') || '';
  const data = ct.includes('application/json') ? await resp.json() : await resp.text();
  if (!resp.ok) { const e = new Error(data?.detail || (typeof data === 'string' ? data : 'فشل الطلب')); e.status = resp.status; throw e; }
  return data;
}

// ... باقی توابعِ (renderMe, refreshTransfers, ...) بدون تغییر می‌مانند ...

// اصلاحات بخش‌های مهم که در متنِ ارسالی تو خراب شده بود:
loginForm.addEventListener('submit', async e=>{e.preventDefault(); const f=new FormData(loginForm); try{const d=await api('/auth/login',{method:'POST',body:JSON.stringify({email: f.get('email'), password: f.get('password')})}); state.token=d.access_token; localStorage.setItem('cloudbell_token', state.token); await loadDashboard();}catch(err){setMessage(err.message,'error');}});

bootstrapForm.addEventListener('submit',async e=>{e.preventDefault(); const f=new FormData(bootstrapForm); try{await api('/auth/bootstrap-admin',{method:'POST',body:JSON.stringify({email: f.get('email'), password: f.get('password')})}); setMessage('تم إنشاء المسؤول. سجل الدخول الآن.');}catch(err){setMessage(err.message,'error');}});

transferForm.addEventListener('submit',async e=>{e.preventDefault(); const f=new FormData(transferForm); submitBtn.disabled=true; submitBtn.textContent='جاري الإرسال…'; try{await api('/transfers',{method:'POST',body:JSON.stringify({url: f.get('url')})}); transferForm.reset(); await refreshTransfers();}catch(err){setMessage(err.message,'error');}finally{submitBtn.disabled=false;submitBtn.textContent='بدء التنزيل';}});
