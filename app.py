import warnings
warnings.filterwarnings("ignore")

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, Response
import json
import os
import secrets
import hashlib
import time
import requests
import re
from functools import wraps
from datetime import datetime, timedelta
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")
DATA_FILE = 'users.json'
MESSAGES_FILE = 'messages.json'
JOURNAL_FILE = 'journal.json'
COURSE_VIDEO_DIR = 'course'
LIVE_DATA_FILE = 'live.json'
GALLERY_DATA_FILE = 'gallery.json'
LIVE_CHAT_FILE = 'live_chat.json'
SIGNALS_FILE = 'signals.json'
GLOBAL_CHAT_FILE = 'global_chat.json'
COURSES_FILE = 'courses.json'
MAINTENANCE_FILE = 'maintenance.json'

# NOWPayments API Configuration
NOWPAYMENTS_API_KEY = "YEW353V-HP0MM01-G4QA7WX-MPDTF62"
NOWPAYMENTS_API_URL = "https://api.nowpayments.io/v1"
COURSE_PRICE_USD = 50

TOTAL_LESSONS = 52

# Track active video sessions
active_sessions = {}

# Track pending crypto payments
pending_payments = {}

# Upload directory for journal screenshots
UPLOAD_DIR = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Upload directory for KYC identity documents
KYC_UPLOAD_DIR = os.path.join('static', 'uploads', 'kyc')
os.makedirs(KYC_UPLOAD_DIR, exist_ok=True)

MANUAL_PAYMENTS_FILE = 'manual_payments.json'

# --- Helpers ---
def load_users():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def load_manual_payments():
    if not os.path.exists(MANUAL_PAYMENTS_FILE):
        return []
    try:
        with open(MANUAL_PAYMENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_manual_payments(data):
    with open(MANUAL_PAYMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def save_users(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_messages():
    if not os.path.exists(MESSAGES_FILE):
        return []
    try:
        with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_messages(messages):
    with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=4, ensure_ascii=False)

def load_journal():
    if not os.path.exists(JOURNAL_FILE):
        return []
    try:
        with open(JOURNAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_journal(entries):
    with open(JOURNAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=4, ensure_ascii=False)

def load_live_data():
    if not os.path.exists(LIVE_DATA_FILE):
        return {"url": "https://www.youtube.com/embed/dQw4w9WgXcQ", "is_live": False, "next_session": "TBD"}
    try:
        with open(LIVE_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"url": "https://www.youtube.com/embed/dQw4w9WgXcQ", "is_live": False, "next_session": "TBD"}

def save_live_data(data):
    with open(LIVE_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_gallery():
    if not os.path.exists(GALLERY_DATA_FILE):
        return []
    try:
        with open(GALLERY_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_gallery(data):
    with open(GALLERY_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_live_chat():
    if not os.path.exists(LIVE_CHAT_FILE):
        return []
    try:
        with open(LIVE_CHAT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_live_chat(data):
    with open(LIVE_CHAT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_signals():
    if not os.path.exists(SIGNALS_FILE):
        return []
    try:
        with open(SIGNALS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_signals(data):
    with open(SIGNALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_global_chat():
    if not os.path.exists(GLOBAL_CHAT_FILE):
        return []
    try:
        with open(GLOBAL_CHAT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_global_chat(data):
    with open(GLOBAL_CHAT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_courses():
    if not os.path.exists(COURSES_FILE):
        return []
    try:
        with open(COURSES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_courses(data):
    with open(COURSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_maintenance():
    if not os.path.exists(MAINTENANCE_FILE):
        return {"enabled": False}
    try:
        with open(MAINTENANCE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"enabled": False}

def save_maintenance(data):
    with open(MAINTENANCE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        users = load_users()
        user = next((u for u in users if u['id'] == session['user_id']), None)
        if not user:
            session.clear()
            return redirect(url_for('login_page'))
        # Admin bypasses KYC
        if user.get('role') != 'admin':
            kyc_status = user.get('kyc_status', 'not_submitted')
            has_files = bool(user.get('kyc_data') and user.get('kyc_data', {}).get('front_image'))
            if kyc_status in ['not_submitted', 'unverified', 'rejected'] or not has_files:
                return redirect(url_for('kyc_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        if session.get('role') != 'admin':
            return "Unauthorized: Admin access required", 403
        return f(*args, **kwargs)
    return decorated_function

def payment_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        users = load_users()
        user = next((u for u in users if u['id'] == session['user_id']), None)
        if not user or not user.get('has_paid', False):
            return redirect(url_for('buy_course'))
        # Admins always have access
        if user.get('role') == 'admin':
            return f(*args, **kwargs)
        # Check subscription expiry if not permanent
        if not user.get('is_permanent', False):
            expiry_date = user.get('expiry_date')
            if expiry_date:
                try:
                    exp_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
                    if datetime.now() > exp_dt:
                        return render_template('expired.html', user=user)
                except:
                    pass
        return f(*args, **kwargs)
    return decorated_function

# --- Maintenance Mode Middleware ---
@app.before_request
def check_maintenance():
    # Allow static files always
    if request.path.startswith('/static'):
        return None
    # Allow maintenance page itself
    if request.path == '/maintenance':
        return None
    # Always allow login/logout so admins can always get back in
    if request.path in ('/', '/login', '/logout', '/api/login', '/api/register'):
        return None
    # Allow admin routes always
    if request.path.startswith('/admin') or request.path.startswith('/api/admin'):
        return None
    # Allow the maintenance toggle API
    if request.path.startswith('/api/maintenance'):
        return None
    # Check if maintenance is enabled
    maintenance = load_maintenance()
    if maintenance.get('enabled', False):
        # Admins bypass maintenance
        if session.get('role') == 'admin':
            return None
        # Redirect everyone else to maintenance page
        return redirect(url_for('maintenance_page'))
    return None

# --- Routes ---

@app.route('/')
def index():
    # Handle referral tracking
    ref_code = request.args.get('ref')
    if ref_code:
        session['referral_code'] = ref_code
    if 'user_id' in session:
        users = load_users()
        user = next((u for u in users if u['id'] == session['user_id']), None)
        if user and user.get('role') != 'admin':
            kyc_status = user.get('kyc_status', 'not_submitted')
            has_files = bool(user.get('kyc_data') and user.get('kyc_data', {}).get('front_image'))
            if kyc_status in ['not_submitted', 'unverified', 'rejected'] or not has_files:
                return redirect(url_for('kyc_page'))
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/login')
def login_page():
    if 'user_id' in session:
        users = load_users()
        user = next((u for u in users if u['id'] == session['user_id']), None)
        if user:
            if user.get('role') == 'admin':
                return redirect(url_for('admin'))
            kyc_status = user.get('kyc_status', 'not_submitted')
            has_files = bool(user.get('kyc_data') and user.get('kyc_data', {}).get('front_image'))
            if kyc_status in ['not_submitted', 'unverified', 'rejected'] or not has_files:
                return redirect(url_for('kyc_page'))
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/kyc')
def kyc_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    if not user:
        return redirect(url_for('login_page'))
    if user.get('role') == 'admin':
        return redirect(url_for('admin'))
    
    kyc_status = user.get('kyc_status', 'not_submitted')
    has_files = bool(user.get('kyc_data') and user.get('kyc_data', {}).get('front_image'))
    
    # If already verified and has files, redirect to home
    if kyc_status == 'verified' and has_files:
        return redirect(url_for('home'))
        
    return render_template('kyc.html', user=user, kyc_status=kyc_status, kyc_data=user.get('kyc_data') or {})

@app.route('/home')
@login_required
def home():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    return render_template('home.html', user=user)

@app.route('/journal')
@login_required
def journal():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    return render_template('journal.html', user=user)

@app.route('/live')
@login_required
def live():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    live_data = load_live_data()
    return render_template('live.html', user=user, live_data=live_data)

@app.route('/gallery')
@login_required
def gallery():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    return render_template('gallery.html', user=user)

@app.route('/profile')
@login_required
def profile():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    # Ensure referral code exists
    if not user.get('referral_code'):
        user['referral_code'] = secrets.token_hex(6)
        save_users(users)
    return render_template('profile.html', user=user)

@app.route('/maintenance')
def maintenance_page():
    # If maintenance is off, redirect to home
    maintenance = load_maintenance()
    if not maintenance.get('enabled', False):
        return redirect(url_for('index'))
    # Admins see admin panel, not maintenance page
    if session.get('role') == 'admin':
        return redirect(url_for('admin'))
    return render_template('maintenance.html')

@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')

@app.route('/admin/payments')
@admin_required
def admin_payments():
    payments = load_manual_payments()
    return render_template('admin_payments.html', payments=payments)

@app.route('/chart')
@login_required
def chart():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    return render_template('chart.html', user=user)

@app.route('/chat')
@login_required
def chat():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    return render_template('chat.html', user=user)

@app.route('/buy-course')
@login_required
def buy_course():
    return render_template('buy.html')

@app.route('/buy-crypto')
@login_required
def buy_crypto():
    return render_template('buy-crypto.html')

@app.route('/course')
@payment_required
def course():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)

    session_token = hashlib.sha256(f"{user['id']}{time.time()}{secrets.token_hex(8)}".encode()).hexdigest()
    session['video_token'] = session_token

    active_sessions[session_token] = {
        'user_id': user['id'],
        'username': user['username'],
        'started_at': time.time()
    }

    courses = load_courses()
    return render_template('course.html', user=user, video_token=session_token, custom_courses=courses)

@app.route('/course-library')
@payment_required
def course_library():
    return redirect(url_for('course'))

@app.route('/stream-video/<int:video_num>')
@payment_required
def stream_video(video_num):
    if 'video_token' not in session or session['video_token'] not in active_sessions:
        return "Unauthorized", 403

    file_extension = 'mkv' if video_num <= 2 else 'mp4'
    video_path = os.path.join(COURSE_VIDEO_DIR, f"{video_num}.{file_extension}")

    if not os.path.exists(video_path):
        return "Video not found", 404

    session_info = active_sessions[session['video_token']]
    print(f"[VIDEO ACCESS] User: {session_info['username']} | Video: {video_num}")

    return send_file(video_path, mimetype=f'video/{file_extension}')

@app.route('/logout')
def logout():
    if 'video_token' in session and session['video_token'] in active_sessions:
        del active_sessions[session['video_token']]
    session.clear()
    return redirect(url_for('index'))

# --- Maintenance API ---

@app.route('/api/maintenance', methods=['GET'])
@admin_required
def get_maintenance():
    return jsonify(load_maintenance())

@app.route('/api/maintenance/toggle', methods=['POST'])
@admin_required
def toggle_maintenance():
    data = load_maintenance()
    data['enabled'] = not data.get('enabled', False)
    save_maintenance(data)
    status = 'تم تفعيل وضع الصيانة 🔧' if data['enabled'] else 'تم إيقاف وضع الصيانة ✅'
    return jsonify({'success': True, 'enabled': data['enabled'], 'message': status})

# --- API ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    users = load_users()

    username = data.get('username')
    password = data.get('password')
    referral_code = session.pop('referral_code', None)

    if not username or not password:
        return jsonify({'success': False, 'message': 'Missing fields'}), 400

    for user in users:
        if user['username'] == username:
            return jsonify({'success': False, 'message': 'User already exists'}), 400

    new_user = {
        'id': (max(u['id'] for u in users) + 1) if users else 1,
        'username': username,
        'password': password,
        'role': 'user',
        'has_paid': False,
        'rank': 'Pup',
        'referral_code': secrets.token_hex(6),
        'referrals': [],
        'referred_by': None,
        'progress': {},
        'completed_lessons': [],
        'kyc_status': 'not_submitted',
        'kyc_data': None
    }

    # If referred by someone
    if referral_code:
        referrer = next((u for u in users if u.get('referral_code') == referral_code), None)
        if referrer:
            new_user['referred_by'] = referrer['id']
            if 'referrals' not in referrer:
                referrer['referrals'] = []
            referrer['referrals'].append(new_user['id'])

    users.append(new_user)
    save_users(users)

    return jsonify({'success': True, 'message': 'Account created successfully!'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    users = load_users()
    username = data.get('username')
    password = data.get('password')

    for user in users:
        if user['username'] == username and user['password'] == password:
            # Track login count and last login
            user['login_count'] = user.get('login_count', 0) + 1
            user['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_users(users)

            session['user_id'] = user['id']
            session['role'] = user.get('role', 'user')

            is_admin = user.get('role') == 'admin'
            kyc_status = user.get('kyc_status', 'not_submitted')
            has_files = bool(user.get('kyc_data') and user.get('kyc_data', {}).get('front_image'))
            require_kyc = (not is_admin) and (kyc_status in ['not_submitted', 'unverified', 'rejected'] or not has_files)
            redirect_url = '/admin' if is_admin else ('/home' if not require_kyc else '/kyc')

            return jsonify({
                'success': True,
                'message': f'Welcome back, {username}!',
                'role': user.get('role', 'user'),
                'kyc_status': kyc_status,
                'require_kyc': require_kyc,
                'redirect': redirect_url
            })

    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/users', methods=['GET', 'POST'])
def manage_users():
    if request.method == 'POST':
        data = request.json
        users = load_users()

        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')
        has_paid = data.get('has_paid', False)
        rank = data.get('rank', 'Pup')
        subscription_days = data.get('subscription_days', 0)
        is_permanent = data.get('is_permanent', False)

        if not username or not password:
            return jsonify({'success': False, 'message': 'Missing fields'}), 400

        for user in users:
            if user['username'] == username:
                return jsonify({'success': False, 'message': 'User already exists'}), 400

        # Calculate expiry_date from subscription_days
        expiry_date = None
        if subscription_days and int(subscription_days) > 0 and not is_permanent:
            expiry_date = (datetime.now() + timedelta(days=int(subscription_days))).strftime('%Y-%m-%d')

        new_user = {
            'id': (max(u['id'] for u in users) + 1) if users else 1,
            'username': username,
            'password': password,
            'role': role,
            'has_paid': has_paid,
            'rank': rank,
            'subscription_days': int(subscription_days) if subscription_days else 0,
            'is_permanent': is_permanent,
            'expiry_date': expiry_date,
            'login_count': 0,
            'last_login': None,
            'referral_code': secrets.token_hex(6),
            'referrals': [],
            'progress': {},
            'completed_lessons': []
        }

        users.append(new_user)
        save_users(users)

        return jsonify({'success': True, 'message': 'User created successfully'})

    return jsonify(load_users())

@app.route('/api/users/export', methods=['GET'])
@admin_required
def export_users():
    try:
        users = load_users()
        json_data = json.dumps(users, indent=4, ensure_ascii=False)
        response = Response(
            json_data,
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=users.json'}
        )
        return response
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/import', methods=['POST'])
@admin_required
def import_users():
    try:
        data = request.json
        new_users = data.get('users', [])

        if not isinstance(new_users, list):
            return jsonify({'success': False, 'message': 'Invalid data format'}), 400

        existing_users = load_users()
        existing_usernames = {u['username'] for u in existing_users}

        added_count = 0
        skipped_count = 0

        max_id = max([u['id'] for u in existing_users], default=0)

        for user_data in new_users:
            if 'username' not in user_data or 'password' not in user_data:
                continue

            if user_data['username'] in existing_usernames:
                skipped_count += 1
                continue

            max_id += 1
            new_user = {
                'id': max_id,
                'username': user_data['username'],
                'password': user_data['password'],
                'role': user_data.get('role', 'user'),
                'has_paid': user_data.get('has_paid', False),
                'rank': user_data.get('rank', 'Pup'),
                'referral_code': secrets.token_hex(6),
                'referrals': [],
                'progress': {},
                'completed_lessons': []
            }

            existing_users.append(new_user)
            existing_usernames.add(new_user['username'])
            added_count += 1

        save_users(existing_users)

        return jsonify({
            'success': True,
            'added': added_count,
            'skipped': skipped_count,
            'message': f'Import completed: {added_count} added, {skipped_count} skipped'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    users = load_users()
    users = [u for u in users if u.get('id') != user_id]
    save_users(users)
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    users = load_users()
    for user in users:
        if user.get('id') == user_id:
            user['username'] = data.get('username', user['username'])
            if 'password' in data:
                user['password'] = data['password']
            user['role'] = data.get('role', user['role'])
            if 'has_paid' in data:
                user['has_paid'] = data['has_paid']
            if 'rank' in data:
                user['rank'] = data['rank']
            # Subscription fields
            if 'is_permanent' in data:
                user['is_permanent'] = data['is_permanent']
            if 'subscription_days' in data:
                user['subscription_days'] = int(data['subscription_days'])
            # Recalculate expiry_date if subscription_days provided
            if 'subscription_days' in data and not data.get('is_permanent', user.get('is_permanent', False)):
                sub_days = int(data['subscription_days'])
                if sub_days > 0:
                    # If there's an existing expiry that's still in the future, extend from it; otherwise from now
                    existing_expiry = user.get('expiry_date')
                    base_date = datetime.now()
                    if existing_expiry:
                        try:
                            exp_dt = datetime.strptime(existing_expiry, '%Y-%m-%d')
                            if exp_dt > datetime.now():
                                base_date = exp_dt
                        except:
                            pass
                    user['expiry_date'] = (base_date + timedelta(days=sub_days)).strftime('%Y-%m-%d')
                else:
                    user['expiry_date'] = None
            if data.get('is_permanent', False):
                user['is_permanent'] = True
                user['expiry_date'] = None
            if 'kyc_status' in data:
                user['kyc_status'] = data['kyc_status']
            save_users(users)
            return jsonify({'success': True, 'message': 'User updated'})
    return jsonify({'success': False, 'message': 'User not found'}), 404

# ========== KYC IDENTITY VERIFICATION APIs ==========

@app.route('/api/kyc/submit', methods=['POST'])
def submit_kyc():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    full_name = request.form.get('full_name', '').strip()
    dob = request.form.get('dob', '').strip()
    country = request.form.get('country', '').strip()
    doc_type = request.form.get('doc_type', 'national_id').strip()

    if not full_name or not dob or not country:
        return jsonify({'success': False, 'message': 'يرجى ملء جميع الحقول المطلوبة (الاسم الكامل، تاريخ الميلاد، الإقامة)'}), 400

    # Calculate age
    age = None
    try:
        birth_date = datetime.strptime(dob, '%Y-%m-%d')
        today = datetime.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except:
        pass

    front_file = request.files.get('front_image')
    back_file = request.files.get('back_image')

    if not front_file or front_file.filename == '':
        return jsonify({'success': False, 'message': 'صورة الوجه الأمامي للهوية مطلوبة'}), 400

    # For national_id and driver_license, back_file is required
    if doc_type in ['national_id', 'driver_license'] and (not back_file or back_file.filename == ''):
        return jsonify({'success': False, 'message': 'صورة الوجه الخلفي للهوية مطلوبة لهذا النوع من الوثائق'}), 400

    allowed_exts = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts

    if not allowed_file(front_file.filename):
        return jsonify({'success': False, 'message': 'صيغة الصورة الأمامية غير مدعومة (فقط JPG, PNG, WEBP)'}), 400

    front_ext = front_file.filename.rsplit('.', 1)[1].lower()
    front_filename = f"user_{user['id']}_front_{secrets.token_hex(6)}.{front_ext}"
    front_path = os.path.join(KYC_UPLOAD_DIR, front_filename)
    front_file.save(front_path)

    back_filename = None
    if back_file and back_file.filename != '':
        if not allowed_file(back_file.filename):
            return jsonify({'success': False, 'message': 'صيغة الصورة الخلفية غير مدعومة'}), 400
        back_ext = back_file.filename.rsplit('.', 1)[1].lower()
        back_filename = f"user_{user['id']}_back_{secrets.token_hex(6)}.{back_ext}"
        back_path = os.path.join(KYC_UPLOAD_DIR, back_filename)
        back_file.save(back_path)

    # Attach KYC data to user and set status
    user['kyc_status'] = 'verified'
    user['kyc_data'] = {
        'full_name': full_name,
        'dob': dob,
        'age': age,
        'country': country,
        'doc_type': doc_type,
        'front_image': f"/static/uploads/kyc/{front_filename}",
        'back_image': f"/static/uploads/kyc/{back_filename}" if back_filename else None,
        'submitted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    save_users(users)

    return jsonify({
        'success': True,
        'message': 'تم رفع مستندات الهوية بنجاح، مرحباً بك في ALPHA!',
        'redirect': '/home'
    })

@app.route('/api/admin/users/<int:user_id>/kyc-status', methods=['POST'])
@admin_required
def admin_set_kyc_status(user_id):
    data = request.json or {}
    new_status = data.get('status')
    if new_status not in ['verified', 'unverified', 'pending', 'not_submitted']:
        return jsonify({'success': False, 'message': 'حالة غير صالحة'}), 400

    users = load_users()
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return jsonify({'success': False, 'message': 'المستخدم غير موجود'}), 404

    user['kyc_status'] = new_status
    save_users(users)
    return jsonify({
        'success': True,
        'message': f"تم تحديث حالة التوثيق للمستخدم #{user_id} إلى: {new_status}",
        'kyc_status': new_status
    })

@app.route('/api/admin/users/<int:user_id>/toggle-kyc', methods=['POST'])
@admin_required
def admin_toggle_kyc(user_id):
    users = load_users()
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return jsonify({'success': False, 'message': 'المستخدم غير موجود'}), 404

    current = user.get('kyc_status', 'not_submitted')
    new_status = 'unverified' if current == 'verified' else 'verified'
    user['kyc_status'] = new_status
    save_users(users)

    status_arabic = 'متوثق ✅' if new_status == 'verified' else 'غير متوثق ❌'
    return jsonify({
        'success': True,
        'message': f"تم تغيير حالة الحساب إلى {status_arabic}",
        'kyc_status': new_status
    })

@app.route('/api/admin/kyc/download/<int:user_id>/<side>', methods=['GET'])
@admin_required
def admin_download_kyc_file(user_id, side):
    users = load_users()
    user = next((u for u in users if u['id'] == user_id), None)
    if not user or not user.get('kyc_data'):
        return "بيانات الهوية غير موجودة", 404

    kyc = user['kyc_data']
    image_rel = kyc.get('front_image') if side == 'front' else kyc.get('back_image')
    if not image_rel:
        return "الصورة غير متوفرة", 404

    filename = os.path.basename(image_rel)
    file_path = os.path.join(KYC_UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        file_path = os.path.join('static', 'uploads', 'kyc', filename)
        if not os.path.exists(file_path):
            return "الملف غير موجود على السيرفر", 404

    doc_type = kyc.get('doc_type', 'id')
    download_name = f"KYC_{user['username']}_{doc_type}_{side}_{filename}"
    return send_file(file_path, as_attachment=True, download_name=download_name)

@app.route('/api/subscription-status', methods=['GET'])
@login_required
def subscription_status():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    if not user:
        return jsonify({'success': False}), 404

    is_permanent = user.get('is_permanent', False)
    is_admin = user.get('role') == 'admin'
    expiry_date = user.get('expiry_date')
    days_remaining = None
    is_expired = False

    if not is_permanent and not is_admin and expiry_date:
        try:
            exp_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
            delta = (exp_dt - datetime.now()).days
            days_remaining = max(0, delta)
            is_expired = datetime.now() > exp_dt
        except:
            pass

    return jsonify({
        'success': True,
        'is_permanent': is_permanent,
        'is_admin': is_admin,
        'expiry_date': expiry_date,
        'days_remaining': days_remaining,
        'is_expired': is_expired,
        'login_count': user.get('login_count', 0),
        'last_login': user.get('last_login')
    })

@app.route('/api/confirm-payment', methods=['POST'])
@login_required
def confirm_payment():
    users = load_users()
    for user in users:
        if user['id'] == session['user_id']:
            user['has_paid'] = True
            save_users(users)
            return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'User not found'}), 404

# ========== PROGRESS TRACKING ==========

@app.route('/api/progress', methods=['GET'])
@login_required
def get_progress():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    if not user:
        return jsonify({'success': False}), 404
    completed = user.get('completed_lessons', [])
    return jsonify({
        'success': True,
        'completed_lessons': completed,
        'total_lessons': TOTAL_LESSONS,
        'percentage': round((len(completed) / TOTAL_LESSONS) * 100, 1) if TOTAL_LESSONS > 0 else 0
    })

@app.route('/api/progress/<int:lesson_num>', methods=['POST'])
@login_required
def mark_lesson_complete(lesson_num):
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    if not user:
        return jsonify({'success': False}), 404

    if 'completed_lessons' not in user:
        user['completed_lessons'] = []

    if lesson_num not in user['completed_lessons']:
        user['completed_lessons'].append(lesson_num)
        save_users(users)

    completed = user['completed_lessons']
    return jsonify({
        'success': True,
        'completed_lessons': completed,
        'total_lessons': TOTAL_LESSONS,
        'percentage': round((len(completed) / TOTAL_LESSONS) * 100, 1)
    })

@app.route('/api/progress/<int:lesson_num>', methods=['DELETE'])
@login_required
def unmark_lesson(lesson_num):
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    if not user:
        return jsonify({'success': False}), 404

    completed = user.get('completed_lessons', [])
    if lesson_num in completed:
        completed.remove(lesson_num)
        user['completed_lessons'] = completed
        save_users(users)

    return jsonify({
        'success': True,
        'completed_lessons': completed,
        'total_lessons': TOTAL_LESSONS,
        'percentage': round((len(completed) / TOTAL_LESSONS) * 100, 1)
    })

# ========== TRADING JOURNAL ==========

@app.route('/api/journal', methods=['GET'])
@login_required
def get_journal():
    entries = load_journal()
    user_entries = [e for e in entries if e.get('user_id') == session['user_id']]
    return jsonify({'success': True, 'entries': user_entries})

@app.route('/api/journal', methods=['POST'])
@login_required
def add_journal_entry():
    try:
        entries = load_journal()
        users = load_users()
        user = next((u for u in users if u['id'] == session['user_id']), None)

        # Handle file upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    image_filename = f"journal_{session['user_id']}_{int(time.time())}{ext}"
                    file.save(os.path.join(UPLOAD_DIR, image_filename))

        new_entry = {
            'id': int(time.time() * 1000),
            'user_id': session['user_id'],
            'username': user['username'] if user else 'Unknown',
            'asset': request.form.get('asset', ''),
            'strategy': request.form.get('strategy', 'SMC'),
            'entry_price': request.form.get('entry_price', ''),
            'exit_price': request.form.get('exit_price', ''),
            'outcome': request.form.get('outcome', 'Win'),
            'notes': request.form.get('notes', ''),
            'image': image_filename,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        entries.append(new_entry)
        save_journal(entries)

        return jsonify({'success': True, 'entry': new_entry})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/journal/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_journal_entry(entry_id):
    entries = load_journal()
    entry = next((e for e in entries if e['id'] == entry_id and e['user_id'] == session['user_id']), None)
    if entry and entry.get('image'):
        img_path = os.path.join(UPLOAD_DIR, entry['image'])
        if os.path.exists(img_path):
            os.remove(img_path)
    entries = [e for e in entries if not (e['id'] == entry_id and e['user_id'] == session['user_id'])]
    save_journal(entries)
    return jsonify({'success': True})

# ========== LIVE ROOM & GALLERY APIs ==========

@app.route('/api/admin/live', methods=['POST'])
@admin_required
def update_live_settings():
    data = request.json
    live_data = {
        "url": data.get('url', ''),
        "is_live": data.get('is_live', False),
        "next_session": data.get('next_session', '')
    }
    save_live_data(live_data)
    return jsonify({'success': True, 'message': 'Live settings updated'})

@app.route('/api/gallery', methods=['POST'])
@login_required
def upload_gallery_image():
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image part'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    title = request.form.get('title', 'Untitled')
    date = request.form.get('date', time.strftime('%Y-%m-%d'))
    gallery_type = request.form.get('type', 'wins')

    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)

    # Only admins can upload to the 'zones' section
    if gallery_type == 'zones':
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required for Zones uploads'}), 403

    ext = os.path.splitext(file.filename)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        image_filename = f"gallery_{int(time.time())}{ext}"
        file.save(os.path.join(UPLOAD_DIR, image_filename))
        
        gallery = load_gallery()
        gallery.append({
            'id': int(time.time() * 1000),
            'title': title,
            'date': date,
            'type': gallery_type,
            'user_id': user['id'] if user else 0,
            'username': user['username'] if user else 'Unknown',
            'image': image_filename
        })
        save_gallery(gallery)
        return jsonify({'success': True, 'message': 'Gallery image uploaded'})
    else:
        return jsonify({'success': False, 'message': 'Invalid file type'}), 400

@app.route('/api/gallery', methods=['GET'])
@login_required
def get_gallery():
    return jsonify({'success': True, 'gallery': load_gallery()})

@app.route('/api/gallery/<int:image_id>', methods=['DELETE'])
@admin_required
def delete_gallery_image(image_id):
    gallery = load_gallery()
    entry = next((e for e in gallery if e['id'] == image_id), None)
    if entry and entry.get('image'):
        img_path = os.path.join(UPLOAD_DIR, entry['image'])
        if os.path.exists(img_path):
            os.remove(img_path)
    gallery = [e for e in gallery if e['id'] != image_id]
    save_gallery(gallery)
    return jsonify({'success': True})

@app.route('/api/live/chat', methods=['GET'])
@login_required
def get_live_chat():
    messages = load_live_chat()
    # Return last 50 messages
    return jsonify({'success': True, 'messages': messages[-50:]})

@app.route('/api/live/chat', methods=['POST'])
@login_required
def post_live_chat():
    data = request.json
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'message': 'Empty message'}), 400

    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    messages = load_live_chat()
    
    new_msg = {
        'id': int(time.time() * 1000),
        'user_id': user['id'],
        'username': user['username'],
        'rank': user.get('rank', 'Pup'),
        'content': content,
        'timestamp': time.strftime('%H:%M:%S')
    }
    
    messages.append(new_msg)
    if len(messages) > 200:
        messages = messages[-200:]
    save_live_chat(messages)

    return jsonify({'success': True, 'message': new_msg})

# ========== REFERRAL SYSTEM ==========

@app.route('/api/referral', methods=['GET'])
@login_required
def get_referral():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    if not user:
        return jsonify({'success': False}), 404

    if not user.get('referral_code'):
        user['referral_code'] = secrets.token_hex(6)
        save_users(users)

    referrals = user.get('referrals', [])
    referral_users = [u for u in users if u['id'] in referrals]
    paid_referrals = [u for u in referral_users if u.get('has_paid', False)]

    base_url = request.host_url.rstrip('/')
    referral_link = f"{base_url}/?ref={user['referral_code']}"

    commission_per_referral = 10  # USD per paid referral
    total_commission = len(paid_referrals) * commission_per_referral

    return jsonify({
        'success': True,
        'referral_code': user['referral_code'],
        'referral_link': referral_link,
        'total_referrals': len(referrals),
        'paid_referrals': len(paid_referrals),
        'total_commission': total_commission,
        'referral_users': [{'username': u['username'], 'has_paid': u.get('has_paid', False)} for u in referral_users]
    })

# ========== CRYPTO PAYMENT ENDPOINTS ==========

@app.route('/create-crypto-payment', methods=['POST'])
@login_required
def create_crypto_payment():
    try:
        data = request.json
        crypto_currency = data.get('crypto', 'btc').lower()

        valid_cryptos = ['btc', 'eth', 'usdttrc20', 'ltc', 'bnbbsc', 'usdcbsc']
        if crypto_currency not in valid_cryptos:
            return jsonify({'success': False, 'message': 'Invalid cryptocurrency'}), 400

        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'User not authenticated'}), 401

        tier = data.get('tier', 'Pro')
        price_mapping = {'Starter': 30, 'Pro': 60, 'VIP': 150}
        price = price_mapping.get(tier, 60)

        payment_data = {
            "price_amount": price,
            "price_currency": "usd",
            "pay_currency": crypto_currency,
            "ipn_callback_url": "https://alpha-project.onrender.com/nowpayments-webhook",
            "order_id": f"user_{user_id}_{int(time.time())}",
            "order_description": f"ALPHA Course ({tier}) - User {user_id}"
        }

        headers = {
            "x-api-key": NOWPAYMENTS_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{NOWPAYMENTS_API_URL}/payment",
            json=payment_data,
            headers=headers,
            timeout=10
        )

        if response.status_code == 201:
            payment_info = response.json()
            payment_id = payment_info.get('payment_id')
            pending_payments[payment_id] = {
                'user_id': user_id,
                'status': 'waiting',
                'created_at': time.time()
            }

            return jsonify({
                'success': True,
                'payment_id': payment_id,
                'pay_address': payment_info.get('pay_address'),
                'pay_amount': payment_info.get('pay_amount'),
                'pay_currency': payment_info.get('pay_currency').upper(),
                'order_id': payment_info.get('order_id'),
                'payment_status': payment_info.get('payment_status')
            })
        else:
            error_msg = response.json().get('message', 'Payment creation failed')
            return jsonify({'success': False, 'message': error_msg}), 400

    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'message': f'API Error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server Error: {str(e)}'}), 500

@app.route('/nowpayments-webhook', methods=['POST'])
def nowpayments_webhook():
    try:
        data = request.json
        payment_status = data.get('payment_status')
        order_description = data.get('order_description', '')
        payment_id = data.get('payment_id')

        print(f"[WEBHOOK] Payment ID: {payment_id} | Status: {payment_status}")

        match = re.search(r'User (\d+)', order_description)
        if not match:
            return jsonify({'success': False, 'message': 'Invalid order description'}), 400

        user_id = int(match.group(1))

        if payment_id in pending_payments:
            pending_payments[payment_id]['status'] = payment_status

        if payment_status in ['confirmed', 'finished']:
            users = load_users()
            for user in users:
                if user['id'] == user_id:
                    user['has_paid'] = True
                    user['subscription_status'] = 'Active'
                    user['payment_method'] = 'Crypto'
                    
                    # Try to extract the tier from the order_description
                    tier_match = re.search(r'\((.*?)\)', order_description)
                    if tier_match:
                        user['tier'] = tier_match.group(1)
                    
                    save_users(users)
                    print(f"[WEBHOOK] ✅ Access granted to user {user_id}")
                    break

        return jsonify({'success': True}), 200

    except Exception as e:
        print(f"[WEBHOOK ERROR] {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/manual-payment', methods=['POST'])
@login_required
def manual_payment():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    tier = request.form.get('tier', 'Pro')
    
    if 'receipt' not in request.files:
        return jsonify({'success': False, 'message': 'No receipt uploaded'}), 400
    
    file = request.files['receipt']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Empty file'}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        return jsonify({'success': False, 'message': 'Invalid image format'}), 400
        
    date_str = time.strftime('%Y%m%d_%H%M%S')
    filename = f"{user['id']}_{date_str}{ext}"
    receipts_dir = os.path.join(UPLOAD_DIR, 'receipts')
    os.makedirs(receipts_dir, exist_ok=True)
    file_path = os.path.join(receipts_dir, filename)
    file.save(file_path)
    
    payments = load_manual_payments()
    payments.append({
        'id': int(time.time() * 1000),
        'user_id': user['id'],
        'username': user['username'],
        'tier': tier,
        'amount': {'Starter': 30, 'Pro': 60, 'VIP': 150}.get(tier, 60),
        'receipt': f"receipts/{filename}",
        'status': 'Pending',
        'date': time.strftime('%Y-%m-%d %H:%M:%S')
    })
    save_manual_payments(payments)
    
    # Update user status
    user['subscription_status'] = 'Pending'
    user['payment_method'] = 'Vodafone Cash'
    save_users(users)
    
    return jsonify({'success': True, 'message': 'Payment submitted successfully'})

@app.route('/api/admin/payments/<action>/<int:payment_id>', methods=['POST'])
@admin_required
def manage_payment(action, payment_id):
    payments = load_manual_payments()
    payment = next((p for p in payments if p['id'] == payment_id), None)
    if not payment:
        return jsonify({'success': False, 'message': 'Payment not found'}), 404
        
    users = load_users()
    user = next((u for u in users if u['id'] == payment['user_id']), None)
        
    if action == 'approve':
        if user:
            user['has_paid'] = True
            user['subscription_status'] = 'Active'
            user['payment_method'] = 'Vodafone Cash'
            user['tier'] = payment['tier']
            save_users(users)
        
        # Remove receipt file
        receipt_path = os.path.join(UPLOAD_DIR, 'receipts', os.path.basename(payment['receipt']))
        if os.path.exists(receipt_path):
            os.remove(receipt_path)
            
        payments = [p for p in payments if p['id'] != payment_id]
        save_manual_payments(payments)
        return jsonify({'success': True, 'message': 'Payment approved'})
        
    elif action == 'reject':
        if user:
            user['subscription_status'] = 'Rejected'
            save_users(users)
            
        # Remove receipt file
        receipt_path = os.path.join(UPLOAD_DIR, 'receipts', os.path.basename(payment['receipt']))
        if os.path.exists(receipt_path):
            os.remove(receipt_path)
            
        payments = [p for p in payments if p['id'] != payment_id]
        save_manual_payments(payments)
        return jsonify({'success': True, 'message': 'Payment rejected, user notified'})
    
    return jsonify({'success': False, 'message': 'Invalid action'}), 400

@app.route('/check-payment/<int:payment_id>', methods=['GET'])
@login_required
def check_payment(payment_id):
    try:
        headers = {"x-api-key": NOWPAYMENTS_API_KEY}

        response = requests.get(
            f"{NOWPAYMENTS_API_URL}/payment/{payment_id}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            payment_data = response.json()
            payment_status = payment_data.get('payment_status')

            user_id = session.get('user_id')
            users = load_users()
            user = next((u for u in users if u['id'] == user_id), None)
            has_access = user.get('has_paid', False) if user else False

            return jsonify({
                'success': True,
                'payment_status': payment_status,
                'has_access': has_access,
                'pay_amount': payment_data.get('pay_amount'),
                'actually_paid': payment_data.get('actually_paid'),
                'updated_at': payment_data.get('updated_at')
            })
        else:
            return jsonify({'success': False, 'message': 'Payment not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    return jsonify(load_messages())

@app.route('/api/messages', methods=['POST'])
@admin_required
def send_message():
    data = request.json
    content = data.get('content')
    if not content:
        return jsonify({'success': False, 'message': 'Empty message'}), 400

    messages = load_messages()

    if len(messages) > 100:
        messages = messages[-100:]

    new_msg = {
        'id': int(time.time() * 1000),
        'sender': 'Admin',
        'content': content,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }

    messages.append(new_msg)
    save_messages(messages)

    return jsonify({'success': True, 'message': 'Message sent'})

# ========== NEW APIS (CHAT & SIGNALS) ==========

@app.route('/api/chat', methods=['GET'])
@login_required
def get_global_chat():
    messages = load_global_chat()
    return jsonify({'success': True, 'messages': messages[-50:]})

@app.route('/api/chat', methods=['POST'])
@login_required
def post_global_chat():
    data = request.json
    content = data.get('content', '').strip()
    if not content:
         return jsonify({'success': False, 'message': 'Empty message'}), 400

    users = load_users()
    user = next((u for u in users if u['id'] == session.get('user_id')), None)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    messages = load_global_chat()
    new_msg = {
        'id': int(time.time() * 1000),
        'user_id': user['id'],
        'username': user['username'],
        'rank': user.get('rank', 'Pup'),
        'content': content,
        'timestamp': time.strftime('%H:%M:%S')
    }
    messages.append(new_msg)
    if len(messages) > 200:
        messages = messages[-200:]
    save_global_chat(messages)
    return jsonify({'success': True, 'message': new_msg})

@app.route('/api/signals', methods=['GET'])
@login_required
def get_signals():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    # Enforce subscription expiry for non-admin, non-permanent users
    if user and user.get('role') != 'admin' and not user.get('is_permanent', False):
        expiry_date = user.get('expiry_date')
        if expiry_date:
            try:
                exp_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
                if datetime.now() > exp_dt:
                    return jsonify({'success': False, 'message': 'Subscription expired', 'expired': True}), 403
            except:
                pass
    return jsonify({'success': True, 'signals': load_signals()})

@app.route('/api/signals', methods=['POST'])
@admin_required
def post_signal():
    data = request.json
    signals = load_signals()
    new_signal = {
        'id': int(time.time() * 1000),
        'asset': data.get('asset', ''),
        'entry_price': data.get('entry_price', ''),
        'stop_loss': data.get('stop_loss', ''),
        'take_profit': data.get('take_profit', ''),
        'status': data.get('status', 'Active'),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    signals.append(new_signal)
    save_signals(signals)
    return jsonify({'success': True, 'signal': new_signal})

@app.route('/api/signals/<int:signal_id>', methods=['PUT'])
@admin_required
def update_signal(signal_id):
    data = request.json
    signals = load_signals()
    for sig in signals:
        if sig['id'] == signal_id:
            sig['status'] = data.get('status', sig['status'])
            save_signals(signals)
            return jsonify({'success': True})
    return jsonify({'success': False}), 404

@app.route('/api/signals/<int:signal_id>', methods=['DELETE'])
@admin_required
def delete_signal(signal_id):
    signals = load_signals()
    signals = [s for s in signals if s['id'] != signal_id]
    save_signals(signals)
    return jsonify({'success': True})


# ========== COURSES MANAGEMENT API ==========

@app.route('/api/courses', methods=['GET'])
def get_user_courses():
    """Get all courses for authorized users."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    if not user or (not user.get('has_paid', False) and user.get('role') != 'admin'):
        return jsonify({'success': False, 'message': 'Payment required'}), 403
    courses = load_courses()
    return jsonify({'success': True, 'courses': courses})


@app.route('/api/admin/courses', methods=['GET'])
@admin_required
def get_courses():
    """Get all courses with their videos."""
    courses = load_courses()
    return jsonify({'success': True, 'courses': courses})

@app.route('/api/admin/courses', methods=['POST'])
@admin_required
def create_course():
    """Create a new course."""
    data = request.json or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    if not title:
        return jsonify({'success': False, 'message': 'Course title is required'}), 400

    courses = load_courses()
    new_course = {
        'id': int(time.time() * 1000),
        'title': title,
        'description': description,
        'videos': [],
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    courses.append(new_course)
    save_courses(courses)
    return jsonify({'success': True, 'course': new_course})

@app.route('/api/admin/courses/<int:course_id>', methods=['PUT'])
@admin_required
def update_course(course_id):
    """Update course title/description."""
    data = request.json or {}
    courses = load_courses()
    course = next((c for c in courses if c['id'] == course_id), None)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    if 'title' in data:
        course['title'] = data['title'].strip()
    if 'description' in data:
        course['description'] = data['description'].strip()
    save_courses(courses)
    return jsonify({'success': True, 'course': course})

@app.route('/api/admin/courses/<int:course_id>', methods=['DELETE'])
@admin_required
def delete_course(course_id):
    """Delete a course and all its videos."""
    courses = load_courses()
    courses = [c for c in courses if c['id'] != course_id]
    save_courses(courses)
    return jsonify({'success': True})

@app.route('/api/admin/courses/<int:course_id>/videos', methods=['POST'])
@admin_required
def add_video(course_id):
    """Add a video (embed URL) to a course."""
    data = request.json or {}
    title = data.get('title', '').strip()
    embed_url = data.get('embed_url', '').strip()
    if not embed_url:
        return jsonify({'success': False, 'message': 'Embed URL is required'}), 400

    courses = load_courses()
    course = next((c for c in courses if c['id'] == course_id), None)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    new_video = {
        'id': int(time.time() * 1000),
        'title': title or f"Video {len(course.get('videos', [])) + 1}",
        'embed_url': embed_url,
        'added_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    if 'videos' not in course:
        course['videos'] = []
    course['videos'].append(new_video)
    save_courses(courses)
    return jsonify({'success': True, 'video': new_video})

@app.route('/api/admin/courses/<int:course_id>/videos/<int:video_id>', methods=['PUT'])
@admin_required
def update_video(course_id, video_id):
    """Update a video's title or embed URL."""
    data = request.json or {}
    courses = load_courses()
    course = next((c for c in courses if c['id'] == course_id), None)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    video = next((v for v in course.get('videos', []) if v['id'] == video_id), None)
    if not video:
        return jsonify({'success': False, 'message': 'Video not found'}), 404

    if 'title' in data:
        video['title'] = data['title'].strip()
    if 'embed_url' in data:
        video['embed_url'] = data['embed_url'].strip()
    save_courses(courses)
    return jsonify({'success': True, 'video': video})

@app.route('/api/admin/courses/<int:course_id>/videos/<int:video_id>', methods=['DELETE'])
@admin_required
def delete_video(course_id, video_id):
    """Delete a video from a course."""
    courses = load_courses()
    course = next((c for c in courses if c['id'] == course_id), None)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    course['videos'] = [v for v in course.get('videos', []) if v['id'] != video_id]
    save_courses(courses)
    return jsonify({'success': True})

@app.route('/api/admin/courses/export', methods=['GET'])
@admin_required
def export_courses():
    """Download all courses (with video embed URLs) as a JSON backup file."""
    try:
        courses = load_courses()
        json_data = json.dumps(courses, indent=4, ensure_ascii=False)
        response = Response(
            json_data,
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=courses_backup.json'}
        )
        return response
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/courses/import', methods=['POST'])
@admin_required
def import_courses():
    """Import courses from a JSON backup file (merges by title, skips duplicates)."""
    try:
        data = request.json or {}
        incoming = data.get('courses', [])
        if not isinstance(incoming, list):
            return jsonify({'success': False, 'message': 'Invalid format: expected a list of courses'}), 400

        existing = load_courses()
        existing_titles = {c['title'].lower() for c in existing}
        max_id = max([c['id'] for c in existing], default=0)

        added = 0
        skipped = 0
        for course in incoming:
            if not course.get('title'):
                continue
            if course['title'].lower() in existing_titles:
                skipped += 1
                continue
            max_id += 1
            new_course = {
                'id': max_id,
                'title': course['title'],
                'description': course.get('description', ''),
                'videos': course.get('videos', []),
                'created_at': course.get('created_at', time.strftime('%Y-%m-%d %H:%M:%S'))
            }
            # Re-assign video IDs to avoid collisions
            vid_max = int(time.time() * 1000)
            for i, v in enumerate(new_course['videos']):
                v['id'] = vid_max + i + 1
            existing.append(new_course)
            existing_titles.add(new_course['title'].lower())
            added += 1

        save_courses(existing)
        return jsonify({
            'success': True,
            'added': added,
            'skipped': skipped,
            'message': f'Import completed: {added} added, {skipped} skipped'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/gallery', methods=['POST'])
@admin_required
def admin_upload_gallery():
    """Admin-specific gallery upload endpoint used by the admin panel."""
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image part'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400

    title = request.form.get('title', 'Untitled')
    date  = request.form.get('date', time.strftime('%Y-%m-%d'))
    gallery_type = request.form.get('type', 'wins')

    ext = os.path.splitext(file.filename)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        image_filename = f"gallery_{int(time.time())}{ext}"
        file.save(os.path.join(UPLOAD_DIR, image_filename))
        gallery = load_gallery()
        gallery.append({
            'id': int(time.time() * 1000),
            'title': title,
            'date': date,
            'type': gallery_type,
            'user_id': session.get('user_id', 0),
            'username': 'Admin',
            'image': image_filename
        })
        save_gallery(gallery)
        return jsonify({'success': True, 'message': 'Gallery image uploaded'})
    return jsonify({'success': False, 'message': 'Invalid file type'}), 400

# ========== WEBRTC SIGNALING ==========

@socketio.on('join_broadcast')
def handle_join_broadcast(data):
    role = data.get('role', 'viewer')
    if role == 'admin':
        join_room('broadcaster')
    else:
        join_room('viewers')
        emit('viewer_joined', {'id': request.sid}, to='broadcaster')

@socketio.on('offer')
def handle_offer(data):
    emit('offer', data, to=data['target'])

@socketio.on('answer')
def handle_answer(data):
    emit('answer', data, to='broadcaster')

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    target = data.get('target')
    if target == 'broadcaster':
        emit('ice_candidate', data, to='broadcaster')
    else:
        emit('ice_candidate', data, to=target)

@socketio.on('disconnect')
def handle_disconnect():
    emit('viewer_left', {'id': request.sid}, to='broadcaster')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=======================================================")
    print(f"🚀 ALPHA Platform is running successfully!")
    print(f"👉 Local URL: http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
