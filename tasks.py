from celery import Celery
from config import Config
from time import sleep
from models import db, Booking, User
import smtplib
import os

celery = Celery(__name__, broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)

def send_email(to_email, subject, body):
    # Simple SMTP send - relies on env vars from config
    import smtplib
    from email.mime.text import MIMEText
    from config import Config
    if not Config.MAIL_SERVER or not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
        print('Mail settings not configured; skipping send.')
        return
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = Config.MAIL_FROM or Config.MAIL_USERNAME
    msg['To'] = to_email
    try:
        s = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT)
        if Config.MAIL_USE_TLS:
            s.starttls()
        s.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
        s.send_message(msg)
        s.quit()
    except Exception as e:
        print('Failed to send email:', e)

@celery.task
def send_booking_confirmation_email(to_email, booking_id):
    # lightweight task: resolve booking and send simple message
    from models import db, Booking
    # In a real deployment you'd create app context. Keep simple for local demo.
    body = f'Your booking (id={booking_id}) has been confirmed.'
    send_email(to_email, 'Booking confirmation', body)
    return True

@celery.task
def send_review_prompt_email(to_email, booking_id):
    body = f'Please review your recent booking (id={booking_id}).'
    send_email(to_email, 'Please review your booking', body)
    return True
