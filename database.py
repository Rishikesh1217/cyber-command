import sqlite3
import os
import time

DB_NAME = "security_system.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    # Create OTPs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS otps (
        email TEXT PRIMARY KEY,
        otp TEXT NOT NULL,
        expires_at REAL NOT NULL
    )
    ''')
    
    # Create Auth Logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS auth_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        event_type TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        status TEXT NOT NULL,
        location TEXT NOT NULL
    )
    ''')
    
    # Seed a default admin user if not exists
    cursor.execute("SELECT * FROM users WHERE email='admin@example.com'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("admin@example.com", "password123"))
    conn.commit()
    conn.close()

def verify_user(email, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def save_otp(email, otp):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    expires_at = time.time() + 300  # 5 minutes expiry
    cursor.execute("INSERT OR REPLACE INTO otps (email, otp, expires_at) VALUES (?, ?, ?)", (email, otp, expires_at))
    conn.commit()
    conn.close()

def verify_otp_db(email, otp):
    conn = sqlite3.connect(DB_NAME)
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO auth_logs (email, event_type, timestamp, status, location) VALUES (?, ?, ?, ?, ?)",
                   (email, event_type, timestamp, status, location))
    conn.commit()
    conn.close()

def get_logs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auth_logs ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
