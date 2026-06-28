import requests
import random

BREVO_API_KEY = ""
SENDER_EMAIL = ""  

def generate_otp() -> str:
    return str(random.randint(1000, 9999))

def send_otp_email(receiver_email: str, otp_code: str):
    url = "https://api.brevo.com/v3/smtp/email"
    
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    html_body = f"""
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
    
    payload = {
        "sender": {"name": "STATION CHAT", "email": SENDER_EMAIL},
        "to": [{"email": receiver_email}],
        "subject": "Verification Code - ChatApp ✦",
        "htmlContent": html_body
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201, 202]:
            print("Email sent successfully via Brevo API!")
            return True
        else:
            print(f"Brevo Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
