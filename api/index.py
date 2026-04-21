import sys
import os
import sqlite3
import random
import time
import traceback
from flask import Flask, request, jsonify, make_response, send_from_directory

# --- CONFIGURATION ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password"
DB_PATH = "/tmp/security_system.db"
# Path to static files
PUBLIC_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public')

app = Flask(__name__)

# --- STATIC FILE SERVING ---
@app.route('/')
@app.route('/api/index.py')
def serve_index():
    return send_from_directory(PUBLIC_FOLDER, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(PUBLIC_FOLDER, path)

# --- DATABASE LOGIC (INLINED) ---
def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS otps (
            email TEXT PRIMARY KEY,
            otp TEXT NOT NULL,
            expires_at REAL NOT NULL
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS auth_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            location TEXT NOT NULL
        )''')
        cursor.execute("SELECT * FROM users WHERE email='admin@example.com'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("admin@example.com", "password123"))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB INIT ERROR: {e}")
        return False

# Lazy-init the DB
init_db()

def verify_user(email, password):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def save_otp(email, otp):
    conn = get_db_conn()
    cursor = conn.cursor()
    expires_at = time.time() + 300
    cursor.execute("INSERT OR REPLACE INTO otps (email, otp, expires_at) VALUES (?, ?, ?)", (email, otp, expires_at))
    conn.commit()
    conn.close()

def verify_otp_db(email, otp):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT otp, expires_at FROM otps WHERE email=?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        stored_otp, expires_at = row
        if stored_otp == otp and time.time() < expires_at:
            return True
    return False

def add_log(email, event_type, status, location="Mumbai, IN"):
    conn = get_db_conn()
    cursor = conn.cursor()
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO auth_logs (email, event_type, timestamp, status, location) VALUES (?, ?, ?, ?, ?)",
                   (email, event_type, timestamp, status, location))
    conn.commit()
    conn.close()

def get_logs():
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auth_logs ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- UTILS ---
def cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.after_request
def after_request(response):
    return cors(response)

@app.route('/api/<path:path>', methods=['OPTIONS'])
def options(path):
    return cors(make_response('', 204))

def send_email(target_email, otp):
    if SENDER_EMAIL == "your-email@gmail.com":
        print(f"DEMO MODE: OTP for {target_email} is {otp}")
        return False
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = target_email
        msg['Subject'] = "Your 2FA Verification Code"
        body = f"<html><body><h2>OTP: <b>{otp}</b></h2><p>Valid 5 mins.</p></body></html>"
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# --- ROUTES ---
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "db": os.path.exists(DB_PATH)})

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json(silent=True) or {}
        email = data.get('email', '')
        password = data.get('password', '')
        if verify_user(email, password):
            otp = str(random.randint(100000, 999999))
            save_otp(email, otp)
            success = send_email(email, otp)
            return jsonify({
                "success": True, 
                "message": "OTP sent", 
                "email_sent": success,
                "mock_otp": otp if not success else None
            })
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json(silent=True) or {}
        email = data.get('email', '')
        otp = data.get('otp', '')
        if verify_otp_db(email, otp):
            add_log(email, "2FA-OTP", "success")
            return jsonify({"success": True, "message": "Verification successful"})
        add_log(email, "2FA-OTP", "error")
        return jsonify({"success": False, "message": "Invalid or expired OTP"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard-data', methods=['GET'])
def dashboard_data():
    try:
        rows = get_logs()
        formatted_logs = [{
            "id": f"AUTH-{r[0]}",
            "method": r[2],
            "time": r[3],
            "status": r[4],
            "loc": r[5]
        } for r in rows]
        return jsonify({"logs": formatted_logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
