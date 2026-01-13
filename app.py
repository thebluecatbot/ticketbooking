import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from config import Config
from models import db, User, Venue, Event, Seat, Booking, BookingSeat, Review
from datetime import datetime
import csv
from io import StringIO
from tasks import send_booking_confirmation_email, send_review_prompt_email

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
    def index():
        events = Event.query.order_by(Event.date).all()
        return render_template('index.html', events=events)

    @app.route('/register', methods=['GET','POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            if User.query.filter((User.username==username) | (User.email==email)).first():
                flash('Username or email already exists', 'danger')
                return redirect(url_for('register'))
            u = User(username=username, email=email)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            flash('Registered — please log in', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/login', methods=['GET','POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            u = User.query.filter_by(username=username).first()
            if u and u.check_password(password):
                login_user(u)
                flash('Logged in', 'success')
                return redirect(url_for('index'))
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logged out', 'info')
        return redirect(url_for('index'))

    @app.route('/event/<int:event_id>')
    def event_detail(event_id):
        event = Event.query.get_or_404(event_id)
        # show seats from venue
        seats = Seat.query.filter_by(venue_id=event.venue_id).order_by(Seat.seat_number).all()
        return render_template('event_detail.html', event=event, seats=seats)

    @app.route('/book/<int:event_id>', methods=['POST'])
    @login_required
    def book(event_id):
        event = Event.query.get_or_404(event_id)
        seat_ids = request.form.getlist('seats')
        if not seat_ids:
            flash('No seats selected', 'warning')
            return redirect(url_for('event_detail', event_id=event_id))

        try:
            # transaction to avoid double-booking
            with db.session.begin_nested():
                seats = Seat.query.filter(Seat.id.in_(seat_ids)).with_for_update().all()
                # Check all seats are available
                unavailable = [s.seat_number for s in seats if s.status != 'available']
                if unavailable:
                    flash(f'Some seats were already booked: {unavailable}', 'danger')
                    db.session.rollback()
                    return redirect(url_for('event_detail', event_id=event_id))

                # mark seats booked
                for s in seats:
                    s.status = 'booked'

                booking = Booking(user_id=current_user.id, event_id=event.id)
                db.session.add(booking)
                db.session.flush()  # get booking.id

                for s in seats:
                    bs = BookingSeat(booking_id=booking.id, seat_id=s.id)
                    db.session.add(bs)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Booking failed. Try again.', 'danger')
            return redirect(url_for('event_detail', event_id=event_id))

        # Enqueue emails
        send_booking_confirmation_email.delay(current_user.email, booking.id)
        send_review_prompt_email.apply_async(args=[current_user.email, booking.id], countdown=60*60*24)  # 24 hours later

        flash('Booking successful', 'success')
        return redirect(url_for('index'))

    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        if not current_user.is_admin:
            flash('Admin only', 'danger')
            return redirect(url_for('index'))
        total_seats = Seat.query.count()
        booked_seats = Seat.query.filter_by(status='booked').count()
        bookings = Booking.query.order_by(Booking.created_at.desc()).limit(100).all()
        return render_template('admin_dashboard.html', total_seats=total_seats, booked_seats=booked_seats, bookings=bookings)

    @app.route('/admin/export.csv')
    @login_required
    def export_csv():
        if not current_user.is_admin:
            flash('Admin only', 'danger')
            return redirect(url_for('index'))

        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['booking_id','user','event','created_at','seat_numbers'])
        bookings = Booking.query.all()
        for b in bookings:
            seats = [bs.seat.seat_number for bs in b.booking_seats]
            cw.writerow([b.id, b.user.username, b.event.name, b.created_at.isoformat(), ';'.join(map(str,seats))])
        output = si.getvalue()
        return send_file(
            StringIO(output),
            mimetype='text/csv',
            as_attachment=True,
            download_name='bookings_export.csv'
        )

    @app.route('/review/<int:booking_id>', methods=['GET','POST'])
    @login_required
    def review(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        if booking.user_id != current_user.id:
            flash('Not allowed', 'danger')
            return redirect(url_for('index'))
        if request.method == 'POST':
            rating = int(request.form['rating'])
            text = request.form.get('text','')
            review = Review(user_id=current_user.id, booking_id=booking.id, event_id=booking.event_id, venue_id=booking.event.venue_id, rating=rating, text=text)
            db.session.add(review)
            db.session.commit()
            flash('Review submitted', 'success')
            return redirect(url_for('index'))
        return render_template('review.html', booking=booking)

    return app

def init_db():
    app = create_app()
    with app.app_context():
        db.create_all()
        # seed admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('adminpass')
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    create_app().run(debug=True)
