from flask import session, redirect, url_for, render_template
from datetime import datetime
from config import users_collection, admins_collection, vehicles_collection, jobs_collection

def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('route_login'))
    
    current_admin = session['username']
    
    # Get all non-admin users for the dropdown
    all_regular_users = list(users_collection.find({
        'is_admin': {'$ne': True}
    }).sort('username', 1))
    
    # For backward compatibility, still provide the filtered list
    # but we'll use all_regular_users for the report dropdown
    regular_users = all_regular_users
    
    # Get active vehicles only for users created by this admin
    active_vehicles = list(vehicles_collection.find({
        'handled_by': {'$in': [user.get('username', '') for user in regular_users if user.get('username')]},
        'checkout_time': None
    }).sort('checkin_time', -1))
    
    # Get admin users
    admin_users = list(admins_collection.find().sort('created_at', -1))
    
    # Get total users count for this admin
    total_users = len(regular_users)
    
    # Get today's check-ins count for users created by this admin
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    todays_checkins = vehicles_collection.count_documents({
        'handled_by': {'$in': [user.get('username', '') for user in regular_users if user.get('username')]},
        'checkin_time': {'$gte': today_start}
    })
    
    # Get delivery jobs created by this admin
    delivery_jobs = list(jobs_collection.find({
        'created_by': current_admin
    }).sort('created_at', -1))

    return render_template('admin_dashboard.html',
                         regular_users=regular_users,
                         admin_users=admin_users,
                         active_vehicles=active_vehicles,
                         current_user=current_admin,
                         total_users=total_users,
                         todays_checkins=todays_checkins,
                         delivery_jobs=delivery_jobs) 