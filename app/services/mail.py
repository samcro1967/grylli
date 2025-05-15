import smtplib
from email.mime.text import MIMEText
import os

def send_email(to, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = os.environ["EMAIL_FROM"]
    msg['To'] = to

    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if os.environ.get("SMTP_USE_TLS", "1") == "1":
            server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
