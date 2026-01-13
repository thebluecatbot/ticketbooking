# Ticket Booking Web Application

Simple Flask-based ticket booking app (seat-level booking) with:
- Flask + SQLAlchemy (SQLite)
- Flask-Login auth
- Celery tasks (Redis broker)
- SMTP email hooks (configured via environment variables)
- Admin read-only dashboard and CSV export

## Quick start (local)

1. Create a virtualenv and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Set environment variables (example):
   ```
   export FLASK_APP=app.py
   export FLASK_ENV=development
   export SECRET_KEY='replace-with-a-secret'
   export DATABASE_URL='sqlite:///data.db'
   export CELERY_BROKER_URL='redis://localhost:6379/0'
   export MAIL_SERVER='smtp.example.com'
   export MAIL_PORT=587
   export MAIL_USERNAME='you@example.com'
   export MAIL_PASSWORD='password'
   export MAIL_USE_TLS=1
   ```

3. Start Redis (required by Celery) and run Celery worker:
   ```
   redis-server
   celery -A celery_worker.celery worker --loglevel=info
   ```

4. Initialize the database:
   ```
   python -c "from app import init_db; init_db()"
   ```

5. Run the Flask app:
   ```
   flask run
   ```

6. Open http://127.0.0.1:5000

## Notes / Limitations
- Uses SQLite for local testing; not suited for high concurrency.
- Celery requires a broker (Redis recommended).
- Passwords are hashed but this is a simple example; review security before production.
