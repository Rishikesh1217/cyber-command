from flask import Flask, request, jsonify, send_from_directory
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import os
try:
    from . import database
    from . import config
except ImportError:
    import database
    import config
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: index.html is actually in the parent directory
PARENT_DIR = os.path.dirname(BASE_DIR)
app = Flask(__name__, static_folder=PARENT_DIR, template_folder=PARENT_DIR)
CORS(app)

# Initialize Database
database.init_db()

@app.route('/')
def index():
    return send_from_directory(PARENT_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(PARENT_DIR, filename)

def send_email(target_email, otp):
    try:
        msg = MIMEMultipart()
        msg['From'] = config.SENDER_EMAIL
        msg['To'] = target_email
        msg['Subject'] = "Your 2FA Verification Code"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="background-color: #ffffff; border-radius: 8px; padding: 40px; max-width: 600px; margin: auto; border: 1px solid #e0e0e0;">
                <h2 style="color: #3b82f6;">Security Verification</h2>
                <p>Hello,</p>
                <p>You are receiving this email because a sign-in attempt was made for your account.</p>
                <div style="background-color: #eff6ff; border-radius: 4px; padding: 20px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #3b82f6;">{otp}</span>
                </div>
                <p>This code is valid for 5 minutes. If you did not initiate this request, please secure your account immediately.</p>
                <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 30px 0;">
                <p style="font-size: 12px; color: #999999;">This is an automated security notification from 2FA Secure Portal.</p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    # Database-backed authentication check
    print(f"Login attempt for: {email}") # Debug log
    if database.verify_user(email, password):
        otp = str(random.randint(100000, 999999))
        database.save_otp(email, otp)
        
        # Try to send real email
        success = send_email(email, otp)
        
        return jsonify({
            "success": True, 
            "message": "OTP sent successfully", 
            "email_sent": success,
            "mock_otp": otp if not success else None
        })
    else:
        print(f"Invalid login for: {email}") # Debug log
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')
    
    if database.verify_otp_db(email, otp):
        database.add_log(email, "2FA-OTP", "success")
        return jsonify({"success": True, "message": "Verification successful"})
    else:
        database.add_log(email, "2FA-OTP", "error")
        return jsonify({"success": False, "message": "Invalid or expired OTP"}), 401

@app.route('/api/dashboard-data', methods=['GET'])
def dashboard_data():
    logs = database.get_logs()
    # Format logs for frontend
    formatted_logs = []
    for log in logs:
        formatted_logs.append({
            "id": f"AUTH-{log[0]}",
            "method": log[2],
            "time": log[3],
            "status": log[4],
            "loc": log[5]
        })
    return jsonify({"logs": formatted_logs})

if __name__ == '__main__':
    print("Starting Cyber Command Server on http://localhost:5000")
    app.run(port=5001, debug=True)
