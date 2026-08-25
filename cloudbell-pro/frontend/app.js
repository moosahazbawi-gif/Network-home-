const state = { token: localStorage.getItem('cloudbell_token') || '', me: null };
const el = (id) => document.getElementById(id);
const authMessage = el('authMessage'), bootstrapForm = el('bootstrapForm'), loginForm = el('loginForm');
const transferForm = el('transferForm'), appPanel = el('appPanel'), logoutBtn = el('logoutBtn');
const meBox = el('meBox'), transfersBox = el('transfers'), refreshBtn = el('refreshBtn');
const submitBtn = transferForm.querySelector('button[type="submit"]');

function setMessage(text, kind = 'info') { authMessage.textContent = text; authMessage.className = `message ${kind}`; }
function authHeaders() { const h = { 'Content-Type': 'application/json' }; if (state.token) h.Authorization = `Bearer ${state.token}`; return h; }
async function api(path, options = {}) {
  const resp = await fetch(`/api${path}`, { ...options, headers: { ...authHeaders(), ...(options.headers || {}) } });
  const ct = resp.headers.get('content-type') || '';
  const data = ct.includes('application/json') ? await resp.json() : await resp.text();
  if (!resp.ok) { const e = new Error(data?.detail || (typeof data === 'string' ? data : 'فشل الطلب')); e.status = resp.status; throw e; }
  return data;
}
function escapeHtml(v) { return String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function formatBytes(bytes) { if (!bytes) return '—'; const u=['بايت','KB','MB','GB','TB']; let n=bytes,i=0; while(n>=1024&&i<u.length-1){n/=1024;i++;} return `${n.toFixed(i?1:0)} ${u[i]}`; }
function statusLabel(s) { return ({queued:'في الانتظار',running:'جاري التنزيل',completed:'اكتمل',failed:'فشل',canceled:'ملغى',expired:'منتهي'})[s] || s; }
function statusClass(s) { return ['completed','failed','canceled','expired','running'].includes(s) ? s : 'queued'; }

function renderMe() {
  meBox.innerHTML = `<div class="profile-card"><div class="avatar">${escapeHtml((state.me.email||'?')[0].toUpperCase())}</div><div class="profile-main"><strong>${escapeHtml(state.me.email)}</strong><span>${state.me.is_admin?'مسؤول النظام':'مستخدم'}</span></div><div class="profile-meta"><div><small>رقم الحساب</small><b>#${state.me.id}</b></div><div><small>تاريخ الإنشاء</small><b>${new Date(state.me.created_at).toLocaleDateString('ar')}</b></div></div></div>`;
}

async function refreshTransfers() {
  refreshBtn.disabled = true;
  try {
    const items = await api('/transfers'); transfersBox.innerHTML = '';
    if (!items.length) { transfersBox.innerHTML = '<div class="empty"><div class="empty-icon">↓</div><strong>لا توجد تنزيلات بعد</strong><span>ضع رابط ملف في الأعلى لبدء أول تنزيل.</span></div>'; return; }
    const wrap = document.createElement('div'); wrap.className='table';
    for (const item of items) {
      const row=document.createElement('section'); row.className='row';
      row.innerHTML=`<div class="row-head"><div class="file-title"><span class="file-icon">↧</span><div><strong>${escapeHtml(item.safe_filename||item.source_url)}</strong><div class="meta">#${item.id} · ${new Date(item.created_at).toLocaleString('ar')}</div></div></div><span class="status ${statusClass(item.status)}">${statusLabel(item.status)}</span></div><div class="progress-line ${item.status==='running'?'active':''}"><span></span></div><div class="transfer-info"><span>${formatBytes(item.byte_size)}</span><span>${item.error_message?escapeHtml(item.error_message):escapeHtml(item.source_url)}</span></div><div class="actions"></div>`;
      const actions=row.querySelector('.actions');
      if(item.status==='completed'){const dl=document.createElement('a'); dl.className='button-link'; dl.href=`/api/transfers/${item.id}/file`; dl.textContent='تحميل الملف'; actions.appendChild(dl);}
      if(item.status==='queued'||item.status==='running'){const c=document.createElement('button'); c.className='ghost'; c.textContent='إلغاء'; c.onclick=async()=>{await api(`/transfers/${item.id}/cancel`,{method:'POST'});await refreshTransfers();}; actions.appendChild(c);}
      wrap.appendChild(row);
    }
    transfersBox.appendChild(wrap);
  } finally { refreshBtn.disabled=false; }
}
async function loadDashboard(){ state.me=await api('/auth/me'); renderMe(); appPanel.classList.remove('hidden'); logoutBtn.classList.remove('hidden'); bootstrapForm.classList.add('hidden'); loginForm.closest('.auth-panel').classList.add('hidden'); await refreshTransfers(); }

loginForm.addEventListener('submit', async e=>{e.preventDefault();const f=new FormData(loginForm);try{const d=await api('/auth/login',{method:'POST',body:JSON.stringify({email:f.get('email'),password:f.get('password')})});state.token=d.access_token;localStorage.setItem('cloudbell_token',state.token);await loadDashboard();}catch(err){setMessage(err.message,'error');}});
bootstrapForm.addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(bootstrapForm);try{await api('/auth/bootstrap-admin',{method:'POST',body:JSON.stringify({email:f.get('email'),password:f.get('password')})});setMessage('تم إنشاء المسؤول. سجل الدخول الآن.');}catch(err){setMessage(err.message,'error');}});
transferForm.addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(transferForm);submitBtn.disabled=true;submitBtn.textContent='جاري الإرسال…';try{await api('/transfers',{method:'POST',body:JSON.stringify({url:f.get('url')})});transferForm.reset();await refreshTransfers();}catch(err){setMessage(err.message,'error');}finally{submitBtn.disabled=false;submitBtn.textContent='بدء التنزيل';}});
refreshBtn.addEventListener('click',refreshTransfers);
logoutBtn.addEventListener('click',()=>{state.token='';state.me=null;localStorage.removeItem('cloudbell_token');appPanel.classList.add('hidden');logoutBtn.classList.add('hidden');loginForm.closest('.auth-panel').classList.remove('hidden');meBox.innerHTML='';transfersBox.innerHTML='';setMessage('تم تسجيل الخروج.');});
setInterval(()=>{if(state.token&&!appPanel.classList.contains('hidden'))refreshTransfers().catch(()=>{});},5000);
(async()=>{if(!state.token)return;try{await loadDashboard();}catch(err){localStorage.removeItem('cloudbell_token');state.token='';setMessage('انتهت الجلسة. سجل الدخول من جديد.','error');}})();
