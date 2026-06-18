import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "zrkiliya@gmail.com"  
SENDER_PASSWORD = "nueo eowz lkmn gwze"  

def generate_otp() -> str:
    return str(random.randint(1000, 9999))

def send_otp_email(receiver_email: str, otp_code: str):
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = receiver_email
    message["Subject"] = "Verification Code - ChatApp ✦"

    body = f"""
    <html>
        <body style="background-color: #0d0d0d; color: #f0f0f0; font-family: sans-serif; padding: 20px; text-align: center;">
            <h1 style="color: #c8f04a;">STATION ✦</h1>
            <p style="font-size: 1.1rem;">Thank you for registering. Your verification code is:</p>
            <div style="background-color: #161616; border: 1px solid #2a2a2a; display: inline-block; padding: 15px 30px; border-radius: 10px; font-size: 2rem; font-weight: bold; color: #c8f04a; letter-spacing: 5px; margin: 20px 0;">
                {otp_code}
            </div>
            <p style="color: #666; font-size: 0.85rem;">This code will expire shortly.</p>
        </body>
    </html>
    """
    message.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, message.as_string())
        server.close()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False