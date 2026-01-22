const API_BASE = '/api';

// UI Toggles
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
        setTimeout(() => box.style.display = 'none', 3000);
    }
}

function clearMessage() {
    const box = document.getElementById('messageBox');
    if (box) box.style.display = 'none';
}

// Auth Logic
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
                    if (data.role === 'admin' || username === 'admin') { // Simple check for demo
                        window.location.href = '/admin';
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

// Admin Logic
async function loadUsers() {
    const tbody = document.getElementById('userTableBody');
    if (!tbody) return;

    try {
        const res = await fetch(`${API_BASE}/users`);
        const users = await res.json();

        tbody.innerHTML = '';
        users.forEach(user => {
            const tr = document.createElement('tr');
            const statusClass = user.has_paid ? 'status-paid' : 'status-unpaid';
            const statusText = user.has_paid ? 'PAID' : 'FREE';

            tr.innerHTML = `
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.role || 'user'}</td>
                <td><span class="status-badge ${user.has_paid ? 'paid' : 'unpaid'}" style="background: ${user.has_paid ? 'rgba(16, 185, 129, 0.2); color: #10b981' : 'rgba(239, 68, 68, 0.2); color: #ef4444'}; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem;">${user.has_paid ? 'Premium' : 'Free'}</span></td>
                <td>
                    <button class="action-btn btn-edit" onclick="openEdit(${user.id}, '${user.username}', '${user.role || 'user'}', ${user.has_paid})">Edit</button>
                    <button class="action-btn btn-delete" onclick="deleteUser(${user.id})">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed to load users");
    }
}

async function deleteUser(id) {
    if (!confirm('Are you sure you want to delete this user?')) return;

    await fetch(`${API_BASE}/users/${id}`, { method: 'DELETE' });
    loadUsers();
}

// Create User Functions
function openCreateModal() {
    document.getElementById('createUsername').value = '';
    document.getElementById('createPassword').value = '';
    document.getElementById('createRole').value = 'user';
    document.getElementById('createHasPaid').checked = false;
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
        const has_paid = document.getElementById('createHasPaid').checked;

        try {
            const res = await fetch(`${API_BASE}/users`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, role, has_paid })
            });

            if (res.ok) {
                closeCreateModal();
                loadUsers();
                showMessage('User created successfully', 'success');
            } else {
                const data = await res.json();
                alert(data.message || 'Error creating user');
            }
        } catch (err) {
            alert('Failed to create user');
        }
    });
}

// Edit User Functions
function openEdit(id, username, role, hasPaid) {
    document.getElementById('editId').value = id;
    document.getElementById('editUser').value = username;
    document.getElementById('editRole').value = role;
    document.getElementById('editHasPaid').checked = hasPaid;
    document.getElementById('editPass').value = ''; // Don't show old pass
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
        const has_paid = document.getElementById('editHasPaid').checked;

        const payload = { username, role, has_paid };
        if (password) payload.password = password;

        await fetch(`${API_BASE}/users/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        closeModal();
        loadUsers();
    });
}

