#now this my user.py backend file
from flask import Flask, request, jsonify, session, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['vehicle_monitoring']
users_collection = db['users']
jobs_collection = db['jobs']
vehicles_collection = db['vehicles']

# Helper functions
def get_current_user():
    if 'username' in session:
        return users_collection.find_one({'username': session['username']})
    return None

# Routes
@app.route('/route_login', methods=['POST'])
def route_login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = users_collection.find_one({'username': username})

    if user and check_password_hash(user['password'], password):
        session['username'] = username
        flash('Login successful!', 'success')
        return redirect(url_for('home'))
    else:
        flash('Invalid username or password', 'danger')
        return redirect(url_for('login'))

@app.route('/route_logout')
def route_logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/route_checkin', methods=['POST'])
def route_checkin():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    vehicle_number = request.form.get('vehicle_number')
    payment_mode = request.form.get('payment_mode')

    checkin_time = datetime.datetime.now()

    vehicle_data = {
        'vehicle_number': vehicle_number,
        'checkin_time': checkin_time,
        'payment_mode': payment_mode,
        'handled_by': session['username'],
        'status': 'checked_in'
    }

    vehicles_collection.insert_one(vehicle_data)
    flash('Vehicle checked in successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/route_checkout', methods=['POST'])
def route_checkout():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    vehicle_number = request.form.get('vehicle_number')
    payment_mode = request.form.get('payment_mode')

    vehicle = vehicles_collection.find_one({'vehicle_number': vehicle_number, 'status': 'checked_in'})

    if not vehicle:
        flash('Vehicle not found or already checked out', 'danger')
        return redirect(url_for('home'))

    checkout_time = datetime.datetime.now()
    checkin_time = vehicle['checkin_time']
    duration = (checkout_time - checkin_time).total_seconds() / 3600  # in hours

    # Calculate charges based on duration and rates
    user = get_current_user()
    initial_amount = user.get('initial_amount', 15)
    initial_duration = user.get('initial_duration', 1)
    extra_charge = user.get('extra_charge', 10)
    extra_charge_duration = user.get('extra_charge_duration', 1)

    if duration <= initial_duration:
        total_charge = initial_amount
    else:
        extra_hours = duration - initial_duration
        total_charge = initial_amount + (extra_hours // extra_charge_duration) * extra_charge

    vehicles_collection.update_one(
        {'_id': vehicle['_id']},
        {'$set': {
            'checkout_time': checkout_time,
            'payment_mode': payment_mode,
            'total_charge': total_charge,
            'status': 'checked_out'
        }}
    )

    flash(f'Vehicle checked out successfully! Total charge: ₹{total_charge}', 'success')
    return redirect(url_for('home'))

@app.route('/route_create_job', methods=['POST'])
def route_create_job():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    load_from = request.form.get('load_from')
    load_to = request.form.get('load_to')
    load_details = request.form.get('load_details')

    job_data = {
        'load_from': load_from,
        'load_to': load_to,
        'load_details': load_details,
        'status': 'open',
        'created_by': session['username'],
        'created_at': datetime.datetime.now()
    }

    jobs_collection.insert_one(job_data)
    flash('Job created successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/route_assign_job/<job_id>', methods=['POST'])
def route_assign_job(job_id):
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    username = request.form.get('username')

    jobs_collection.update_one(
        {'_id': ObjectId(job_id)},
        {'$set': {
            'assigned_to': username,
            'status': 'assigned'
        }}
    )

    flash('Job assigned successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/route_delete_job/<job_id>', methods=['POST'])
def route_delete_job(job_id):
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    jobs_collection.delete_one({'_id': ObjectId(job_id)})
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/route_create_user', methods=['POST'])
def route_create_user():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    username = request.form.get('username')
    password = request.form.get('password')
    initial_amount = float(request.form.get('initial_amount'))
    initial_duration = int(request.form.get('initial_duration'))
    extra_charge = float(request.form.get('extra_charge'))
    extra_charge_duration = int(request.form.get('extra_charge_duration'))

    if users_collection.find_one({'username': username}):
        flash('Username already exists', 'danger')
        return redirect(url_for('admin_dashboard'))

    user_data = {
        'username': username,
        'password': generate_password_hash(password),
        'initial_amount': initial_amount,
        'initial_duration': initial_duration,
        'extra_charge': extra_charge,
        'extra_charge_duration': extra_charge_duration,
        'created_by': session['username'],
        'created_at': datetime.datetime.now()
    }

    users_collection.insert_one(user_data)
    flash('User created successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/route_delete_user/<username>', methods=['POST'])
def route_delete_user(username):
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    users_collection.delete_one({'username': username})
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/route_generate_report', methods=['POST'])
def route_generate_report():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    report_type = request.form.get('report_type')
    selected_user = request.form.get('selected_user')
    date = request.form.get('date')

    # Implement report generation logic here
    # This is a placeholder for the actual report generation logic
    flash('Report generated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=50001)