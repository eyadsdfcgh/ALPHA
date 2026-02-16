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

// Export Users to JSON
async function exportUsers() {
    try {
        const res = await fetch(`${API_BASE}/users/export`);
        if (!res.ok) {
            throw new Error('Failed to export users');
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `users_backup_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showMessage('Users exported successfully!', 'success');
    } catch (err) {
        console.error(err);
        showMessage('Failed to export users', 'error');
    }
}

// Import Users from JSON
async function importUsers(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.json')) {
        showMessage('Please select a valid JSON file', 'error');
        return;
    }

    try {
        const text = await file.text();
        const users = JSON.parse(text);

        // Validate JSON structure
        if (!Array.isArray(users)) {
            throw new Error('Invalid JSON format: expected an array of users');
        }

        // Validate each user object
        for (const user of users) {
            if (!user.username || !user.password) {
                throw new Error('Invalid user data: username and password are required');
            }
        }

        // Confirm with user
        const confirmMsg = `This will import ${users.length} user(s). Do you want to continue?\n\nNote: Existing users with the same username will be skipped.`;
        if (!confirm(confirmMsg)) {
            event.target.value = ''; // Reset file input
            return;
        }

        // Send to server
        const res = await fetch(`${API_BASE}/users/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ users })
        });

        const data = await res.json();

        if (data.success) {
            showMessage(`Import successful! Added ${data.added} new user(s), skipped ${data.skipped} existing user(s).`, 'success');
            loadUsers();
        } else {
            showMessage(data.message || 'Import failed', 'error');
        }
    } catch (err) {
        console.error(err);
        showMessage(`Import failed: ${err.message}`, 'error');
    } finally {
        event.target.value = ''; // Reset file input
    }
}
