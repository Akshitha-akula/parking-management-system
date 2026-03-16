import os, secrets
from urllib.parse import quote_plus
from datetime import datetime, date, time
from flask import (
    Flask, request, jsonify, render_template,
    redirect, url_for, session, flash
)
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash


# ----------------- Basic setup -----------------
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = secrets.token_hex(32)

# ----------------- Database config -----------------
railway_url = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL")

if railway_url:
    # Railway gives mysql://  — SQLAlchemy needs mysql+mysqlconnector://
    if railway_url.startswith("mysql://"):
        railway_url = railway_url.replace("mysql://", "mysql+mysqlconnector://", 1)
    DB_URI = railway_url
else:
    # Local fallback
    DB_DRIVER = os.getenv("DB_DRIVER", "mysql+mysqlconnector")
    DB_USER   = os.getenv("DB_USER", "root")
    DB_PASS   = quote_plus(os.getenv("DB_PASSWORD", ""))
    DB_HOST   = os.getenv("DB_HOST", "localhost")
    DB_PORT   = os.getenv("DB_PORT", "3306")
    DB_NAME   = os.getenv("DB_NAME", "ParkingManagementSystemDb")

    DB_URI    = f"{DB_DRIVER}://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)



# --------------------- MODELS ----------------------
class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150))
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.String(150))
    firstname = db.Column(db.String(150), nullable=False)
    lastname  = db.Column(db.String(150), nullable=False)
    username  = db.Column(db.String(150), unique=True, nullable=False)
    mobileNumber = db.Column(db.String(30))
    password  = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.String(20))
    dob = db.Column(db.Date)
    memberType = db.Column(db.String(50))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    zipcode = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class Vehicle(db.Model):
    __tablename__ = 'vehicle'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    vehicleId = db.Column(db.String(80), nullable=False)
    owner_name = db.Column(db.String(150), nullable=False)
    vehicle_brand = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True)
    zoneName = db.Column(db.String(100), unique=True, nullable=False)
    totalSlot = db.Column(db.Integer, nullable=False)
    availableSlot = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    bookingDate = db.Column(db.Date, nullable=False)
    zone = db.Column(db.String(100), nullable=False)
    bookingStartTime = db.Column(db.Time, nullable=False)
    bookingEndTime = db.Column(db.Time, nullable=False)
    cardType = db.Column(db.String(40))
    cardName = db.Column(db.String(150))
    cardNumber = db.Column(db.String(32))
    expDate = db.Column(db.String(10))
    cvv = db.Column(db.String(10))
    paymentStatus = db.Column(db.String(40))
    username = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class CanceledBooking(db.Model):
    __tablename__ = 'canceledBooking'
    id = db.Column(db.Integer, primary_key=True)
    bookingDate = db.Column(db.Date, nullable=False)
    zone = db.Column(db.String(100), nullable=False)
    bookingStartTime = db.Column(db.Time, nullable=False)
    bookingEndTime = db.Column(db.Time, nullable=False)
    cardType = db.Column(db.String(40))
    cardName = db.Column(db.String(150))
    cardNumber = db.Column(db.String(32))
    expDate = db.Column(db.String(10))
    cvv = db.Column(db.String(10))
    paymentStatus = db.Column(db.String(40))
    username = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


Booking.__table_args__ = (
    db.UniqueConstraint(
        'username', 'bookingDate', 'bookingStartTime', 'bookingEndTime', 'zone',
        name='uniq_user_slot'
    ),
)


# ----------------- CREATE TABLES + DEFAULT ADMIN -----------------
with app.app_context():
    db.create_all()

    # Create admin only if missing
    if not Admin.query.filter_by(username="admin123@gmail.com").first():
        admin_user = Admin(
            username="admin123@gmail.com",
            name="admin",
            password=generate_password_hash("Admin@123", method="pbkdf2:sha256", salt_length=16),
        )
        db.session.add(admin_user)
        db.session.commit()



# ----------------- ROUTES -----------------

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()

        # Admin login
        admin_user = Admin.query.filter_by(username=username).first()
        if admin_user and check_password_hash(admin_user.password, password):
            session['username'] = admin_user.username
            session['role'] = 'admin'
            return redirect(url_for('admin_home'))

        # User login
        user_user = User.query.filter_by(username=username).first()
        if user_user and check_password_hash(user_user.password, password):
            session['username'] = user_user.username
            session['role'] = 'user'
            return redirect(url_for('user_home'))

        flash('Invalid credentials', 'error')
    return render_template('login.html')



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        username = data.get('username','').strip()

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('signup'))

        u = User(
            userId=data.get('userId'),
            firstname=data.get('firstname'),
            lastname=data.get('lastname'),
            username=username,
            password=generate_password_hash(data.get('password'), method='pbkdf2:sha256', salt_length=16),
            mobileNumber=data.get('mobileNumber'),
            gender=data.get('gender'),
            dob=datetime.strptime(data.get('dob'), "%Y-%m-%d").date() if data.get('dob') else None,
            memberType=data.get('memberType'),
            address=data.get('address'),
            city=data.get('city'),
            zipcode=data.get('zipcode')
        )

        db.session.add(u)
        db.session.commit()
        flash('Signup successful. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')



@app.route('/')
def home():
    role = session.get('role')
    if role == 'admin':
        return redirect(url_for('admin_home'))
    if role == 'user':
        return redirect(url_for('user_home'))
    return render_template('homePage.html')



@app.route('/admin')
def admin_home():
    return render_template('admin_homePage.html')



@app.route('/admin_homePage')
def admin_home_alias():
    return redirect(url_for('admin_home'))



@app.route('/userHome')
@app.route('/slotsHomePage')
def user_home():
    zones = Location.query.order_by(Location.zoneName).all()
    return render_template('slotsHomePage.html', zones=zones)



@app.route('/slots')
@app.route('/book')
@app.route('/book_slot')
@app.route('/bookslot')
@app.route('/bookASlot')
@app.route('/startBooking')
@app.route('/check_in')
def booking_form():
    zones = Location.query.order_by(Location.zoneName).all()
    return render_template('slots.html', zones=zones)



# ----------------- Admin Add Zone -----------------
@app.route('/addZone', methods=['GET','POST'])
def add_zone():
    if request.method == 'GET':
        return render_template('addZone.html')

    data = request.get_json(silent=True) or request.form
    zone_name = (data.get('zoneName') or data.get('zone') or '').strip()
    total_raw = data.get('totalSlot') or data.get('total')

    if not zone_name or not total_raw:
        if request.is_json:
            return jsonify({'message':'zoneName and totalSlot are required'}),400
        flash('zoneName and totalSlot are required','error')
        return redirect(url_for('add_zone'))

    total = int(total_raw)

    if Location.query.filter_by(zoneName=zone_name).first():
        if request.is_json:
            return jsonify({'message':'Zone already exists'}),409
        flash('Zone already exists','error')
        return redirect(url_for('add_zone'))

    z = Location(zoneName=zone_name, totalSlot=total, availableSlot=total)
    db.session.add(z)
    db.session.commit()

    if request.is_json:
        return jsonify({'message':'Zone added successfully!'}),201

    flash('Zone added successfully!','success')
    return redirect(url_for('admin_home'))



@app.route('/zones')
def list_zones():
    zones = Location.query.order_by(Location.zoneName).all()
    return jsonify([{
        'zoneName': z.zoneName, 'totalSlot': z.totalSlot, 'availableSlot': z.availableSlot
    } for z in zones])



@app.route('/allSlots', methods=['GET','POST'])
def all_slots_page():
    zones = Location.query.order_by(Location.zoneName).all()
    selected_zone = None
    slots = []

    if request.method == 'POST':
        selected_zone = request.form.get('zone')
        if selected_zone:
            slots = Booking.query.filter_by(zone=selected_zone).order_by(
                Booking.bookingDate, Booking.bookingStartTime
            ).all()

    return render_template('allSlots.html', zones=zones, zone=selected_zone, slots=slots)



# ----------------- VEHICLES -----------------
@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    data_json = request.get_json(silent=True)

    if data_json:
        vehicle_id = data_json.get('vehicleId')
        owner_name = data_json.get('owner_name') or data_json.get('ownerName')
        vehicle_brand = data_json.get('vehicle_brand') or data_json.get('vehicleBrand')
    else:
        form = request.form
        vehicle_id = form.get('vehicleId')
        owner_name = form.get('ownerName')
        vehicle_brand = form.get('vehicleBrand')

    if not vehicle_id or not owner_name or not vehicle_brand:
        return jsonify({'success':False,'message':'All fields required'}),400

    v = Vehicle(
        username=session['username'],
        vehicleId=vehicle_id,
        owner_name=owner_name,
        vehicle_brand=vehicle_brand
    )
    db.session.add(v)
    db.session.commit()

    return jsonify({'success':True,'message':'Vehicle added successfully'})


@app.route('/vehicle_details')
def vehicle_details():
    if 'username' not in session:
        return redirect(url_for('login'))
    vehicles = Vehicle.query.filter_by(username=session['username']).all()
    return render_template('vehicle_details.html', vehicles=vehicles)


@app.route('/remove_vehicle/<int:vehicle_id>', methods=['POST'])
def remove_vehicle(vehicle_id):
    v = Vehicle.query.get_or_404(vehicle_id)
    db.session.delete(v)
    db.session.commit()
    return jsonify({'success':True,'message':'Vehicle removed successfully'})


# ----------------- PROFILE -----------------
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    return render_template('profile.html', user=user)



# ----------------- BOOKING (AJAX) -----------------
@app.route('/verify_slot', methods=['POST'])
def verify_slot():
    d = request.get_json() or {}
    booking_date = date.fromisoformat(d['bookingDate'])
    start_t = time.fromisoformat(d['bookingStartTime'])
    end_t   = time.fromisoformat(d['bookingEndTime'])
    zone    = d['zone']

    booked = db.session.query(db.func.count(Booking.id)).filter(
        Booking.bookingDate==booking_date,
        Booking.bookingStartTime==start_t,
        Booking.bookingEndTime==end_t,
        Booking.zone==zone
    ).scalar()

    loc = Location.query.filter_by(zoneName=zone).first()
    total = loc.totalSlot if loc else 0

    return jsonify({
        'totalSlots': total,
        'bookedSlots': int(booked or 0),
        'availableSlots': max(0, total - int(booked or 0))
    })



@app.route('/save_booking', methods=['POST'])
def save_booking():
    d = request.get_json() or {}

    # Basic validation
    if not d.get('cardName') or len(d['cardName']) < 3:
        return jsonify({'success':False,'message':'Invalid name'}),400

    if not d.get('cardNumber') or not d['cardNumber'].isdigit() or len(d['cardNumber']) != 16:
        return jsonify({'success':False,'message':'Invalid card number'}),400

    if not d.get('cvv') or not d['cvv'].isdigit() or len(d['cvv']) != 3:
        return jsonify({'success':False,'message':'Invalid CVV'}),400

    b = Booking(
        bookingDate=date.fromisoformat(d['bookingDate']),
        zone=d['zone'],
        bookingStartTime=time.fromisoformat(d['bookingStartTime']),
        bookingEndTime=time.fromisoformat(d['bookingEndTime']),
        cardType=d.get('cardType'),
        cardName=d.get('cardName'),
        cardNumber=d.get('cardNumber'),
        expDate=d.get('expDate'),
        cvv=d.get('cvv'),
        paymentStatus=d.get('paymentStatus','success'),
        username=session['username']
    )

    db.session.add(b)
    db.session.commit()

    return jsonify({'success':True,'message':'Booking saved','bookingId':b.id})



@app.route('/bookings')
def bookings_page():
    my_bookings = Booking.query.filter_by(username=session['username']).order_by(Booking.id).all()
    return render_template('bookings.html', bookings=my_bookings)



@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    d = request.get_json() or {}
    b = Booking.query.get_or_404(int(d['bookingId']))

    start_dt = datetime.combine(b.bookingDate, b.bookingStartTime)
    if (start_dt - datetime.now()).total_seconds() <= 7200:
        return jsonify({'success':False,'message':'Cannot cancel within 2 hours'}),400

    cb = CanceledBooking(
        bookingDate=b.bookingDate, zone=b.zone,
        bookingStartTime=b.bookingStartTime, bookingEndTime=b.bookingEndTime,
        cardType=b.cardType, cardName=b.cardName, cardNumber=b.cardNumber,
        expDate=b.expDate, cvv=b.cvv, paymentStatus=b.paymentStatus,
        username=b.username
    )

    db.session.add(cb)
    db.session.delete(b)
    db.session.commit()

    return jsonify({'success':True,'message':'Booking canceled'})


@app.route('/canceledBooking')
def canceled_bookings_page():
    my_canceled = CanceledBooking.query.filter_by(username=session['username']).order_by(CanceledBooking.id).all()
    return render_template('canceledBooking.html', user_canceled_booking=my_canceled)


@app.route('/canceledBookings')
def canceled_bookings_alias():
    return redirect(url_for('canceled_bookings_page'))


@app.route('/allCanceledBookings')
def all_canceled_bookings_all():
    canceled = CanceledBooking.query.order_by(CanceledBooking.id).all()
    return render_template('allCanceledBookings.html', canceled_bookings=canceled)



# ----------------- ADMIN LISTS -----------------
@app.route('/allCustomers')
def all_customers():
    users = User.query.order_by(User.id).all()
    return render_template('allCustomers.html', users=users)

@app.route('/allVehicles')
def all_vehicles():
    vehicles = Vehicle.query.order_by(Vehicle.id).all()
    return render_template('allVehicles.html', vehicles=vehicles)

@app.route('/allBookings')
def all_bookings():
    bookings = Booking.query.order_by(Booking.id).all()
    return render_template('allBookings.html', bookings=bookings)



# ----------------- START APP -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)
