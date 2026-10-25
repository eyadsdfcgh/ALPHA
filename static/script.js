const API_BASE = '/api';

// ─── UI Helpers ───────────────────────────────────────────────

function showRegister() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('registerSection').style.display = 'block';
    clearMessage();
}

function showLogin() {
    document.getElementById('registerSection').style.display = 'none';
    document.getElementById('loginSection').style.display = 'block';
    clearMessage();
}

function showMessage(msg, type = 'success') {
    const box = document.getElementById('messageBox') || document.getElementById('adminMessage');
    if (box) {
        box.textContent = msg;
        box.className = `message ${type}`;
        box.style.display = 'block';
        setTimeout(() => box.style.display = 'none', 3500);
    }
}

function clearMessage() {
    const box = document.getElementById('messageBox');
    if (box) box.style.display = 'none';
}

// ─── Auth Logic ───────────────────────────────────────────────

const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('loginUser').value;
        const password = document.getElementById('loginPass').value;

        try {
            const res = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();

            if (data.success) {
                showMessage(data.message, 'success');
                setTimeout(() => {
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else if (data.role === 'admin') {
                        window.location.href = '/admin';
                    } else if (data.require_kyc) {
                        window.location.href = '/kyc';
                    } else {
                        window.location.href = '/home';
                    }
                }, 1000);
            } else {
                showMessage(data.message, 'error');
            }
        } catch (err) {
            showMessage('Server connection failed', 'error');
        }
    });
}

const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('regUser').value;
        const password = document.getElementById('regPass').value;

        try {
            const res = await fetch(`${API_BASE}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();

            if (data.success) {
                showMessage(data.message, 'success');
                setTimeout(showLogin, 1500);
            } else {
                showMessage(data.message, 'error');
            }
        } catch (err) {
            showMessage('Server connection failed', 'error');
        }
    });
}

// ─── Subscription Helpers ─────────────────────────────────────

function getDaysRemaining(user) {
    if (user.role === 'admin') return { label: '∞ Admin', cls: 'days-perm' };
    if (user.is_permanent) return { label: '♾️ Lifetime', cls: 'days-perm' };
    if (!user.expiry_date) return { label: '—', cls: 'days-none' };

    const now = new Date();
    const expiry = new Date(user.expiry_date);
    const diff = Math.floor((expiry - now) / (1000 * 60 * 60 * 24));

    if (diff < 0) return { label: 'Expired', cls: 'days-exp' };
    if (diff <= 7) return { label: `⚠️ ${diff}d`, cls: 'days-warn' };
    return { label: `${diff}d`, cls: 'days-ok' };
}

function getStatusBadge(user) {
    if (user.role === 'admin') return '<span class="badge badge-admin">👮 Admin</span>';
    if (user.is_permanent) return '<span class="badge badge-permanent">♾️ Permanent</span>';
    if (!user.has_paid) return '<span class="badge badge-free">Free</span>';

    // Check if expired
    if (user.expiry_date) {
        const diff = Math.floor((new Date(user.expiry_date) - new Date()) / (1000 * 60 * 60 * 24));
        if (diff < 0) return '<span class="badge badge-expired">❌ Expired</span>';
    }

    return '<span class="badge badge-active">✅ Active</span>';
}

function getKycBadge(user) {
    if (user.role === 'admin') return '<span class="badge badge-kyc-verified">🛡️ Admin</span>';
    const status = user.kyc_status || 'not_submitted';
    if (status === 'verified') return '<span class="badge badge-kyc-verified">✅ موثق</span>';
    if (status === 'pending') return '<span class="badge badge-kyc-pending">⏳ قيد المراجعة</span>';
    if (status === 'unverified' || status === 'rejected') return '<span class="badge badge-kyc-unverified">❌ غير موثق</span>';
    return '<span class="badge badge-kyc-none">⚪ لم يقدم</span>';
}

function formatLastLogin(ts) {
    if (!ts) return '<span style="color:var(--text-muted);font-size:0.78rem">Never</span>';
    // Show short date
    const d = new Date(ts.replace(' ', 'T'));
    if (isNaN(d)) return ts;
    return `<span style="font-size:0.78rem;color:var(--text-muted)">${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>`;
}

// ─── Admin: Load Users ────────────────────────────────────────

let currentKycUserId = null;

async function loadUsers() {
    const tbody = document.getElementById('userTableBody');
    if (!tbody) return;

    // Show skeleton
    tbody.innerHTML = Array(5).fill('').map(() =>
        `<tr class="skeleton-row">${Array(11).fill('<td><div class="skeleton-cell" style="width:80%;height:14px;border-radius:4px;"></div></td>').join('')}</tr>`
    ).join('');

    try {
        const res = await fetch(`${API_BASE}/users`);
        const users = await res.json();

        // Update stats
        const total = users.length;
        const perm = users.filter(u => u.is_permanent || u.role === 'admin').length;
        const active = users.filter(u => {
            if (u.role === 'admin' || u.is_permanent) return u.has_paid;
            if (!u.has_paid) return false;
            if (!u.expiry_date) return u.has_paid;
            return new Date(u.expiry_date) > new Date();
        }).length;
        const expired = users.filter(u => {
            if (!u.has_paid || u.is_permanent || u.role === 'admin') return false;
            if (!u.expiry_date) return false;
            return new Date(u.expiry_date) <= new Date();
        }).length;
        const totalLogins = users.reduce((acc, u) => acc + (u.login_count || 0), 0);
        const kycVerified = users.filter(u => u.kyc_status === 'verified').length;
        const kycUnverified = users.filter(u => u.kyc_status !== 'verified' && u.role !== 'admin').length;

        const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        setEl('statTotal', total);
        setEl('statActive', active);
        setEl('statPerm', perm);
        setEl('statExpired', expired);
        setEl('statLogins', totalLogins.toLocaleString());
        setEl('statKycVerified', kycVerified);
        setEl('statKycUnverified', kycUnverified);

        tbody.innerHTML = '';
        users.forEach(user => {
            const tr = document.createElement('tr');
            const days = getDaysRemaining(user);
            const statusBadge = getStatusBadge(user);
            const kycBadge = getKycBadge(user);
            const loginCount = user.login_count || 0;
            const expiryLabel = user.expiry_date
                ? `<span style="font-size:0.75rem;color:var(--text-muted)">${user.expiry_date}</span>`
                : (user.is_permanent ? '<span style="font-size:0.75rem;color:var(--gold)">No expiry</span>' : '<span style="font-size:0.75rem;color:var(--text-muted)">—</span>');

            const isVerified = user.kyc_status === 'verified';
            const toggleKycTitle = isVerified ? 'إلغاء التوثيق (Make Unverified)' : 'توثيق الحساب (Make Verified)';
            const toggleKycIcon = isVerified ? '❌ إيقاف التوثيق' : '✅ توثيق';

            tr.innerHTML = `
                <td style="font-weight:700;color:var(--text-muted)">#${user.id}</td>
                <td style="font-weight:700">${escapeHtml(user.username)}</td>
                <td>${user.role === 'admin' ? '<span class="badge badge-admin">Admin</span>' : '<span style="color:var(--text-muted);font-size:0.82rem">User</span>'}</td>
                <td><span class="badge badge-rank" style="font-size:0.72rem">${escapeHtml(user.rank || 'Pup')}</span></td>
                <td>${statusBadge}</td>
                <td>${kycBadge}</td>
                <td>${expiryLabel}</td>
                <td><span class="days-pill ${days.cls}">${days.label}</span></td>
                <td><span class="login-count-badge">🔑 <span class="count">${loginCount}</span></span></td>
                <td>${formatLastLogin(user.last_login)}</td>
                <td>
                    <div class="action-cell">
                        <button class="btn btn-sm btn-kyc" title="Review KYC" onclick='openKycModal(${JSON.stringify(user)})'>🪪 KYC</button>
                        <button class="btn btn-sm btn-toggle-kyc" title="${toggleKycTitle}" onclick="toggleKyc(${user.id})">${toggleKycIcon}</button>
                        <button class="btn btn-sm btn-edit" title="Edit User" onclick='openEdit(${JSON.stringify(user)})'>✏️</button>
                        <button class="btn btn-sm btn-delete" title="Delete User" onclick="deleteUser(${user.id})">🗑️</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="11" style="text-align:center;color:var(--text-muted);padding:2rem">Failed to load users</td></tr>';
        console.error('Failed to load users', err);
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ─── Delete ───────────────────────────────────────────────────

async function deleteUser(id) {
    if (!confirm(`Delete user #${id}? This cannot be undone.`)) return;
    await fetch(`${API_BASE}/users/${id}`, { method: 'DELETE' });
    loadUsers();
    showMessage('User deleted.', 'success');
}

// ─── Create Modal ─────────────────────────────────────────────

function openCreateModal() {
    document.getElementById('createUsername').value = '';
    document.getElementById('createPassword').value = '';
    document.getElementById('createRole').value = 'user';
    document.getElementById('createRank').value = 'Pup';
    document.getElementById('createHasPaid').checked = false;
    document.getElementById('createIsPermanent').checked = false;
    document.getElementById('createSubDays').value = '';
    document.getElementById('createSubDays').disabled = false;
    document.getElementById('createDaysGroup').style.opacity = '1';
    document.getElementById('createModal').classList.add('visible');
}

function closeCreateModal() {
    document.getElementById('createModal').classList.remove('visible');
}

const createForm = document.getElementById('createForm');
if (createForm) {
    createForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('createUsername').value;
        const password = document.getElementById('createPassword').value;
        const role = document.getElementById('createRole').value;
        const rank = document.getElementById('createRank').value;
        const has_paid = document.getElementById('createHasPaid').checked;
        const is_permanent = document.getElementById('createIsPermanent').checked;
        const subscription_days = parseInt(document.getElementById('createSubDays').value || '0', 10);

        try {
            const res = await fetch(`${API_BASE}/users`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, role, has_paid, rank, subscription_days, is_permanent })
            });

            if (res.ok) {
                closeCreateModal();
                loadUsers();
                showMessage('User created successfully! 🎉', 'success');
            } else {
                const data = await res.json();
                alert(data.message || 'Error creating user');
            }
        } catch (err) {
            alert('Failed to create user');
        }
    });
}

// ─── Edit Modal ───────────────────────────────────────────────

function openEdit(user) {
    document.getElementById('editId').value = user.id;
    document.getElementById('editUser').value = user.username;
    document.getElementById('editRole').value = user.role || 'user';
    document.getElementById('editRank').value = user.rank || 'Pup';
    document.getElementById('editHasPaid').checked = !!user.has_paid;
    document.getElementById('editIsPermanent').checked = !!user.is_permanent;
    document.getElementById('editPass').value = '';
    document.getElementById('editSubDays').value = '';

    // Reflect permanent state
    const perm = !!user.is_permanent;
    document.getElementById('editSubDays').disabled = perm;
    document.getElementById('editDaysGroup').style.opacity = perm ? '0.4' : '1';

    document.getElementById('editModal').classList.add('visible');
}

function closeModal() {
    document.getElementById('editModal').classList.remove('visible');
}

const editForm = document.getElementById('editForm');
if (editForm) {
    editForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('editId').value;
        const username = document.getElementById('editUser').value;
        const password = document.getElementById('editPass').value;
        const role = document.getElementById('editRole').value;
        const rank = document.getElementById('editRank').value;
        const has_paid = document.getElementById('editHasPaid').checked;
        const is_permanent = document.getElementById('editIsPermanent').checked;
        const rawDays = document.getElementById('editSubDays').value;
        const subscription_days = rawDays !== '' ? parseInt(rawDays, 10) : undefined;

        const payload = { username, role, has_paid, rank, is_permanent };
        if (password) payload.password = password;
        if (subscription_days !== undefined) payload.subscription_days = subscription_days;

        try {
            const res = await fetch(`${API_BASE}/users/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                closeModal();
                loadUsers();
                showMessage('User updated successfully!', 'success');
            } else {
                alert(data.message || 'Error updating user');
            }
        } catch (err) {
            alert('Failed to update user');
        }
    });
}

// ─── Export / Import ─────────────────────────────────────────

async function exportUsers() {
    try {
        const res = await fetch(`${API_BASE}/users/export`);
        if (!res.ok) throw new Error('Failed to export');
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `alpha_users_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showMessage('Users exported! 📥', 'success');
    } catch (err) {
        showMessage('Export failed', 'error');
    }
}

async function importUsers(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.json')) {
        showMessage('Please select a valid JSON file', 'error');
        return;
    }

    try {
        const text = await file.text();
        const users = JSON.parse(text);

        if (!Array.isArray(users)) throw new Error('Invalid JSON: expected array');

        for (const user of users) {
            if (!user.username || !user.password) {
                throw new Error('Each user must have username and password');
            }
        }

        if (!confirm(`Import ${users.length} user(s)? Existing usernames will be skipped.`)) {
            event.target.value = '';
            return;
        }

        const res = await fetch(`${API_BASE}/users/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ users })
        });
        const data = await res.json();

        if (data.success) {
            showMessage(`Imported ${data.added} user(s), skipped ${data.skipped}.`, 'success');
            loadUsers();
        } else {
            showMessage(data.message || 'Import failed', 'error');
        }
    } catch (err) {
        showMessage(`Import failed: ${err.message}`, 'error');
    } finally {
        event.target.value = '';
    }
}

// ─── KYC Admin Functions ─────────────────────────────────────

function openKycModal(user) {
    currentKycUserId = user.id;
    const modal = document.getElementById('kycModal');
    if (!modal) return;

    modal.classList.add('visible');
    const loading = document.getElementById('kycModalLoading');
    const body = document.getElementById('kycModalBody');
    if (loading) loading.style.display = 'block';
    if (body) body.style.display = 'none';

    document.getElementById('kycUserDisplay').textContent = `${user.username} (#${user.id})`;
    document.getElementById('kycStatusBadgeDisplay').innerHTML = getKycBadge(user);

    const kyc = user.kyc_data || {};
    const hasData = !!(user.kyc_data && user.kyc_data.front_image);

    document.getElementById('kycFullNameDisplay').textContent = kyc.full_name || '—';
    document.getElementById('kycDobAgeDisplay').textContent = kyc.dob ? `${kyc.dob} (${kyc.age ? kyc.age + ' yrs' : ''})` : '—';
    document.getElementById('kycCountryDisplay').textContent = kyc.country || '—';
    
    let docTypeLabel = kyc.doc_type || '—';
    if (kyc.doc_type === 'id') docTypeLabel = 'بطاقة هوية وطنية (National ID)';
    else if (kyc.doc_type === 'passport') docTypeLabel = 'جواز سفر (Passport)';
    else if (kyc.doc_type === 'license') docTypeLabel = 'رخصة قيادة (Driver License)';
    document.getElementById('kycDocTypeDisplay').textContent = docTypeLabel;
    
    document.getElementById('kycSubmittedAtDisplay').textContent = kyc.submitted_at || '—';

    const frontImg = document.getElementById('kycFrontImg');
    const backImg = document.getElementById('kycBackImg');
    const dlFront = document.getElementById('kycDownloadFrontBtn');
    const dlBack = document.getElementById('kycDownloadBackBtn');

    if (kyc.front_image) {
        frontImg.src = kyc.front_image;
        frontImg.style.display = 'block';
        dlFront.href = `/api/admin/kyc/download/${user.id}/front`;
        dlFront.style.display = 'inline-flex';
    } else {
        frontImg.src = '';
        frontImg.style.display = 'none';
        dlFront.style.display = 'none';
    }

    if (kyc.back_image) {
        backImg.src = kyc.back_image;
        backImg.style.display = 'block';
        dlBack.href = `/api/admin/kyc/download/${user.id}/back`;
        dlBack.style.display = 'inline-flex';
    } else {
        backImg.src = '';
        backImg.style.display = 'none';
        dlBack.style.display = 'none';
    }

    if (loading) loading.style.display = 'none';
    if (body) body.style.display = 'block';
}

function closeKycModal() {
    const modal = document.getElementById('kycModal');
    if (modal) modal.classList.remove('visible');
    currentKycUserId = null;
}

async function toggleKyc(userId) {
    try {
        const res = await fetch(`${API_BASE}/admin/users/${userId}/toggle-kyc`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.success) {
            showMessage(`KYC status changed to: ${data.kyc_status} ✅`, 'success');
            loadUsers();
        } else {
            alert(data.message || 'Failed to toggle KYC status');
        }
    } catch (err) {
        alert('Server error toggling KYC status');
    }
}

async function adminSetKycStatus(status) {
    if (!currentKycUserId) return;
    try {
        const res = await fetch(`${API_BASE}/admin/users/${currentKycUserId}/kyc-status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ kyc_status: status })
        });
        const data = await res.json();
        if (data.success) {
            showMessage(data.message, 'success');
            closeKycModal();
            loadUsers();
        } else {
            alert(data.message || 'Failed to set KYC status');
        }
    } catch (err) {
        alert('Server error setting KYC status');
    }
}

