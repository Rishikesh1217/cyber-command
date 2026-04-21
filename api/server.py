import sys
import os

# Add api directory to path so absolute imports work on Vercel
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify
import random
import database
import config
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize Database on cold start
database.init_db()

def send_email(target_email, otp):
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart()
        msg['From'] = config.SENDER_EMAIL
        msg['To'] = target_email
        msg['Subject'] = "Your 2FA Verification Code"
        body = f"<html><body><h2>Your OTP: <b>{otp}</b></h2><p>Valid for 5 minutes.</p></body></html>"
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    if database.verify_user(email, password):
        otp = str(random.randint(100000, 999999))
        database.save_otp(email, otp)
        success = send_email(email, otp)
        return jsonify({
            "success": True,
            "message": "OTP sent",
            "email_sent": success,
            "mock_otp": otp if not success else None
        })
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')
    if database.verify_otp_db(email, otp):
        database.add_log(email, "2FA-OTP", "success")
        return jsonify({"success": True, "message": "Verification successful"})
    database.add_log(email, "2FA-OTP", "error")
    return jsonify({"success": False, "message": "Invalid or expired OTP"}), 401

@app.route('/api/dashboard-data', methods=['GET'])
def dashboard_data():
    logs = database.get_logs()
    formatted_logs = [{
        "id": f"AUTH-{log[0]}",
        "method": log[2],
        "time": log[3],
        "status": log[4],
        "loc": log[5]
    } for log in logs]
    return jsonify({"logs": formatted_logs})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})
