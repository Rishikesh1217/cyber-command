# SMTP Configuration for Real Email OTP
# For Gmail: 
# 1. Enable 2-Step Verification
# 2. Search for "App Passwords" in your Google Account settings
# 3. Generate an App Password for "Mail" and "Other (Custom name: 2FA System)"
# 4. Use that 16-character password here.

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-email@gmail.com"  # Replace with your email
SENDER_PASSWORD = "your-app-password"  # Replace with your App Password
