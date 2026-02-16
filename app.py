from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, Response
import json
import os
import secrets
import hashlib
import time
import requests
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generates a secure random key for sessions
DATA_FILE = 'users.json'
MESSAGES_FILE = 'messages.json'  # File for global chat messages
COURSE_VIDEO_DIR = 'course'  # Directory containing course videos


# NOWPayments API Configuration
NOWPAYMENTS_API_KEY = "YEW353V-HP0MM01-G4QA7WX-MPDTF62"
NOWPAYMENTS_API_URL = "https://api.nowpayments.io/v1"
COURSE_PRICE_USD = 50  # Price in USD

# Track active video sessions (in-memory, for demo purposes)
# In production, use Redis or database
active_sessions = {}

# Track pending crypto payments (in production, use database)
pending_payments = {}

# --- Helpers ---
def load_users():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

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


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        if session.get('role') != 'admin':
            return "Unauthorized: Admin access required", 403
        return f(*args, **kwargs)
    return decorated_function

def payment_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        
        # Verify fresh state from DB
        users = load_users()
        user = next((u for u in users if u['id'] == session['user_id']), None)
        
        if not user or not user.get('has_paid', False):
            return redirect(url_for('buy_course'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/home')
@login_required
def home():
    # Pass user data to template to conditionally show "Buy" button
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    return render_template('home.html', user=user)

@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')

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
    # Get user info for watermarking
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    
    # Generate unique session token for this viewing session
    session_token = hashlib.sha256(f"{user['id']}{time.time()}{secrets.token_hex(8)}".encode()).hexdigest()
    session['video_token'] = session_token
    
    # Store active session
    active_sessions[session_token] = {
        'user_id': user['id'],
        'username': user['username'],
        'started_at': time.time()
    }
    
    return render_template('course.html', user=user, video_token=session_token)

# Route for standalone course library (index.html in course folder)
@app.route('/course-library')
@payment_required
def course_library():
    # Get user info for watermarking
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    
    # Generate unique session token
    session_token = hashlib.sha256(f"{user['id']}{time.time()}{secrets.token_hex(8)}".encode()).hexdigest()
    session['video_token'] = session_token
    
    # Store active session
    active_sessions[session_token] = {
        'user_id': user['id'],
        'username': user['username'],
        'started_at': time.time()
    }
    
    # Serve the index.html from course folder with template processing
    from flask import render_template_string
    course_index_path = os.path.join(COURSE_VIDEO_DIR, 'index.html')
    
    if os.path.exists(course_index_path):
        with open(course_index_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        return render_template_string(template_content, user=user, video_token=session_token)
    else:
        return "Course library not found", 404

# Secure video streaming endpoint
@app.route('/stream-video/<int:video_num>')
@payment_required
def stream_video(video_num):
    # Verify video token
    if 'video_token' not in session or session['video_token'] not in active_sessions:
        return "Unauthorized", 403
    
    # Determine file extension
    file_extension = 'mkv' if video_num <= 2 else 'mp4'
    video_path = os.path.join(COURSE_VIDEO_DIR, f"{video_num}.{file_extension}")
    
    if not os.path.exists(video_path):
        return "Video not found", 404
    
    # Log access (for monitoring suspicious activity)
    session_info = active_sessions[session['video_token']]
    print(f"[VIDEO ACCESS] User: {session_info['username']} | Video: {video_num}")
    
    # Serve the video file
    return send_file(video_path, mimetype=f'video/{file_extension}')

@app.route('/logout')
def logout():
    # Clean up active session
    if 'video_token' in session and session['video_token'] in active_sessions:
        del active_sessions[session['video_token']]
    session.clear()
    return redirect(url_for('index'))

# --- API ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    users = load_users()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Missing fields'}), 400
        
    for user in users:
        if user['username'] == username:
            return jsonify({'success': False, 'message': 'User already exists'}), 400
            
    new_user = {
        'id': len(users) + 1,
        'username': username,
        'password': password,
        'role': 'user',
        'has_paid': False # Default for new users
    }
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
            # Set Session
            session['user_id'] = user['id']
            session['role'] = user.get('role', 'user')
            return jsonify({
                'success': True, 
                'message': f'Welcome back, {username}!', 
                'role': user.get('role', 'user')
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
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Missing fields'}), 400
            
        for user in users:
            if user['username'] == username:
                return jsonify({'success': False, 'message': 'User already exists'}), 400
                
        new_user = {
            'id': len(users) + 1, # Simple ID generation (better to use max id + 1)
            'username': username,
            'password': password,
            'role': role,
            'has_paid': has_paid
        }
        
        # Ensure unique ID
        if users:
            new_user['id'] = max(u['id'] for u in users) + 1
        else:
            new_user['id'] = 1

        users.append(new_user)
        save_users(users)
        
        return jsonify({'success': True, 'message': 'User created successfully'})

    return jsonify(load_users())

@app.route('/api/users/export', methods=['GET'])
@admin_required
def export_users():
    """Export all users to JSON file"""
    try:
        users = load_users()
        # Create a JSON response with proper formatting
        json_data = json.dumps(users, indent=4, ensure_ascii=False)
        
        # Return as downloadable file
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
    """Import users from JSON file"""
    try:
        data = request.json
        new_users = data.get('users', [])
        
        if not isinstance(new_users, list):
            return jsonify({'success': False, 'message': 'Invalid data format'}), 400
        
        existing_users = load_users()
        existing_usernames = {u['username'] for u in existing_users}
        
        added_count = 0
        skipped_count = 0
        
        # Get max ID
        max_id = max([u['id'] for u in existing_users], default=0)
        
        for user_data in new_users:
            # Validate required fields
            if 'username' not in user_data or 'password' not in user_data:
                continue
            
            # Skip if user already exists
            if user_data['username'] in existing_usernames:
                skipped_count += 1
                continue
            
            # Create new user with proper ID
            max_id += 1
            new_user = {
                'id': max_id,
                'username': user_data['username'],
                'password': user_data['password'],
                'role': user_data.get('role', 'user'),
                'has_paid': user_data.get('has_paid', False)
            }
            
            existing_users.append(new_user)
            existing_usernames.add(new_user['username'])
            added_count += 1
        
        # Save updated users
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
            if 'password' in data: # Only update if password provided
                user['password'] = data['password']
            user['role'] = data.get('role', user['role'])
            if 'has_paid' in data: # Allow updating payment status
                user['has_paid'] = data['has_paid']
            # Note: We don't usually let admins edit 'has_paid' via this simple endpoint, 
            # but we preserve it if not sent
            save_users(users)
            return jsonify({'success': True, 'message': 'User updated'})
    return jsonify({'success': False, 'message': 'User not found'}), 404

@app.route('/api/confirm-payment', methods=['POST'])
@login_required
def confirm_payment():
    # In a real app, verify the 'details' object from PayPal with PayPal API
    # to ensure the payment is legitimate.
    
    users = load_users()
    for user in users:
        if user['id'] == session['user_id']:
            user['has_paid'] = True
            save_users(users)
            return jsonify({'success': True})
            
    return jsonify({'success': False, 'message': 'User not found'}), 404

# ========== CRYPTO PAYMENT ENDPOINTS (NOWPayments) ==========

@app.route('/create-crypto-payment', methods=['POST'])
@login_required
def create_crypto_payment():
    """Create a cryptocurrency payment via NOWPayments"""
    try:
        data = request.json
        crypto_currency = data.get('crypto', 'btc').lower()
        
        # Validate crypto currency
        valid_cryptos = ['btc', 'eth', 'usdttrc20', 'ltc', 'bnbbsc', 'usdcbsc']
        if crypto_currency not in valid_cryptos:
            return jsonify({'success': False, 'message': 'Invalid cryptocurrency'}), 400
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'User not authenticated'}), 401
        
        # Prepare payment request
        payment_data = {
            "price_amount": COURSE_PRICE_USD,
            "price_currency": "usd",
            "pay_currency": crypto_currency,
            "ipn_callback_url": "https://alpha-project.onrender.com/nowpayments-webhook",
            "order_id": f"user_{user_id}_{int(time.time())}",
            "order_description": f"ALPHA Course - User {user_id}"
        }
        
        # Call NOWPayments API
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
            
            # Store payment info temporarily
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
    """Handle NOWPayments IPN webhook"""
    try:
        data = request.json
        
        payment_status = data.get('payment_status')
        order_description = data.get('order_description', '')
        payment_id = data.get('payment_id')
        
        print(f"[WEBHOOK] Payment ID: {payment_id} | Status: {payment_status}")
        
        # Extract user_id from order_description "ALPHA Course - User {user_id}"
        match = re.search(r'User (\d+)', order_description)
        if not match:
            return jsonify({'success': False, 'message': 'Invalid order description'}), 400
        
        user_id = int(match.group(1))
        
        # Update payment status in memory
        if payment_id in pending_payments:
            pending_payments[payment_id]['status'] = payment_status
        
        # If payment confirmed, grant access
        if payment_status in ['confirmed', 'finished']:
            users = load_users()
            for user in users:
                if user['id'] == user_id:
                    user['has_paid'] = True
                    save_users(users)
                    print(f"[WEBHOOK] ✅ Access granted to user {user_id}")
                    break
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"[WEBHOOK ERROR] {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/check-payment/<int:payment_id>', methods=['GET'])
@login_required
def check_payment(payment_id):
    """Check payment status from NOWPayments API"""
    try:
        headers = {
            "x-api-key": NOWPAYMENTS_API_KEY
        }
        
        response = requests.get(
            f"{NOWPAYMENTS_API_URL}/payment/{payment_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            payment_data = response.json()
            payment_status = payment_data.get('payment_status')
            
            # Check if user has been granted access
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
    
    # Optional: limit history size
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
