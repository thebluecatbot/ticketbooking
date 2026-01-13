🎟️ Ticket Booking Web Application

A seat-level ticket booking system built with Flask that allows users to browse events, select specific seats, book tickets, and submit reviews. The system includes admin monitoring, background email jobs, and CSV exports for operational tracking.

Designed for local deployment and small–medium scale usage with strong data integrity and overbooking protection.

🚀 Features
User Features

Browse events by venue and date

Select exact seat numbers

Book multiple seats in one transaction

Secure authentication (hashed passwords)

Submit ratings and text reviews after booking

Review prompt emails after booking

Admin Features

Create venues and events

Seat inventory auto-derived from venue capacity

Read-only dashboard:

Total seats

Booked seats

Booking records

Export bookings as CSV

Booking Safety

Every seat has a status (available / booked)

All seat bookings happen inside database transactions

Uses row locking to prevent race conditions

No overbooking is possible

🧱 Tech Stack
Layer	Technology
Backend	Flask
Auth	Flask-Login
Database	SQLite
ORM	SQLAlchemy
Frontend	HTML, CSS, Jinja2
Background Jobs	Celery
Email	SMTP
Exports	CSV
Deployment	Local
📁 Project Structure
ticket_booking_app/
│
├── app.py               # Flask routes & app setup
├── models.py            # Database models
├── tasks.py             # Celery background jobs
├── celery_worker.py     # Celery worker entrypoint
├── config.py            # App configuration
├── requirements.txt
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── event_detail.html
│   ├── login.html
│   ├── register.html
│   ├── admin_dashboard.html
│   └── review.html
│
└── static/
    └── style.css

⚙️ Setup Instructions
1. Create Virtual Environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

2. Environment Variables
export FLASK_APP=app.py
export SECRET_KEY="your-secret-key"
export DATABASE_URL="sqlite:///data.db"

# Celery
export CELERY_BROKER_URL="redis://localhost:6379/0"

# Email (optional but recommended)
export MAIL_SERVER="smtp.example.com"
export MAIL_PORT=587
export MAIL_USERNAME="you@example.com"
export MAIL_PASSWORD="yourpassword"
export MAIL_USE_TLS=1

3. Start Redis (for Celery)
redis-server

4. Start Celery Worker
celery -A celery_worker.celery worker --loglevel=info

5. Initialize Database
python -c "from app import init_db; init_db()"


This creates all tables and a default admin user:

Username: admin
Password: adminpass

6. Run the Web App
flask run


Open:

http://127.0.0.1:5000

🧪 Booking Flow

User selects event

Chooses specific seat numbers

System locks rows in the seat table

Checks availability

Marks seats as booked

Creates booking record

Sends confirmation email

This guarantees no two users can book the same seat.

📤 CSV Export

Admins can download:

/admin/export.csv


Includes:

Booking ID

User

Event

Date

Seat numbers

⚠️ Known Limitations

Local deployment only

SQLite limits concurrency

No booking cancellation

No real-time seat refresh on frontend

Admin dashboard is read-only

🔮 Planned Improvements

Production deployment (Postgres, Docker)

Booking cancellation & seat release

WebSockets for live seat updates

Admin management controls

Payment gateway integration
