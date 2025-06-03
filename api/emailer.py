import smtplib, ssl
from email.mime.text import MIMEText
import os

def send_email(to_addr:str, subject:str, body:str):
    if not os.getenv.SMTP_USER:
        print('[email] SMTP OFF')
        return
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From']    = os.getenv.SMTP_USER
    msg['To']      = to_addr
    ctx = ssl.create_default_context()
    with smtplib.SMTP(os.getenv.SMTP_SERVER, os.getenv.SMTP_PORT) as s:
        s.starttls(context=ctx)
        s.login(os.getenv.SMTP_USER, os.getenv.SMTP_PASS)
        s.send_message(msg)
        print('[email] sent')
