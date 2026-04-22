import sys
import os
import sqlite3
import random
import time
import traceback

# Base directory is the directory containing api folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, make_response, send_from_directory

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')

DB = "/tmp/cyber.db"
init_error = None

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

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

try:
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS otps (
            email TEXT PRIMARY KEY,
            otp TEXT NOT NULL,
            expires_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            event TEXT,
            timestamp TEXT,
            status TEXT,
            location TEXT
        );
    ''')
    if not conn.execute("SELECT 1 FROM users WHERE email='admin@example.com'").fetchone():
        conn.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                     ("admin@example.com", "password123"))
    conn.commit()
    conn.close()
except Exception as e:
    init_error = traceback.format_exc()

# Static files handled by Vercel

@app.route('/api/health', methods=['GET'])
def health():
    if init_error:
        return jsonify({"status": "error", "init_error": init_error}), 500
    return jsonify({"status": "ok", "time": time.strftime('%H:%M:%S')})

@app.route('/api/login', methods=['POST'])
def login():
    if init_error:
        return jsonify({"success": False, "message": "DB Init Error"}), 500
    data = request.get_json(silent=True) or {}
    email = data.get('email', '')
    password = data.get('password', '')
    conn = get_db()
    user = conn.execute("SELECT 1 FROM users WHERE email=? AND password=?",
                        (email, password)).fetchone()
    conn.close()
    if user:
        otp = str(random.randint(100000, 999999))
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO otps VALUES (?, ?, ?)",
                     (email, otp, time.time() + 300))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "OTP sent", "mock_otp": otp})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    if init_error:
        return jsonify({"success": False, "message": "DB Init Error"}), 500
    data = request.get_json(silent=True) or {}
    email = data.get('email', '')
    otp = data.get('otp', '')
    conn = get_db()
    row = conn.execute("SELECT otp, expires_at FROM otps WHERE email=?", (email,)).fetchone()
    conn.close()
    if row and row['otp'] == otp and time.time() < row['expires_at']:
        conn = get_db()
        conn.execute("INSERT INTO logs VALUES (NULL,?,?,?,?,?)",
                     (email, "2FA-OTP", time.strftime('%Y-%m-%d %H:%M:%S'), "success", "Mumbai, IN"))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Verification successful"})
    return jsonify({"success": False, "message": "Invalid or expired OTP"}), 401

@app.route('/api/dashboard-data', methods=['GET'])
def dashboard_data():
    if init_error:
        return jsonify({"error": "DB Init Error"}), 500
    conn = get_db()
    rows = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return jsonify({"logs": [{"id": f"AUTH-{r['id']}", "method": r['event'],
                               "time": r['timestamp'], "status": r['status'],
                               "loc": r['location']} for r in rows]})
