import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

print("🛰️ Attempting secure connection to your mail server...")
try:
    msg = MIMEText("Testing AlphaDeals local loop connection setup.")
    msg['Subject'] = "Pipeline Test"
    msg['From'] = os.getenv("EMAIL_HOST_USER")
    msg['To'] = "info@puescuproperties.com"

    # Force secure Port 587 TLS Connection execution
    server = smtplib.SMTP(os.getenv("EMAIL_SMTP_SERVER"), int(os.getenv("EMAIL_SMTP_PORT")))
    server.starttls() # The critical security handshake
    server.login(os.getenv("EMAIL_HOST_USER"), os.getenv("EMAIL_PASSWORD"))
    server.sendmail(os.getenv("EMAIL_HOST_USER"), ["info@puescuproperties.com"], msg.as_string())
    server.quit()
    print("🚀 BOOM! Connection successful. Check your inbox right now!")
except Exception as e:
    print(f"❌ Connection Failed. Mail Server Error Log:\n{e}")