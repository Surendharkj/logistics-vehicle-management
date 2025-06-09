#now this my job.py backend file
from datetime import datetime
from flask import request, session, flash, redirect, url_for
from bson import ObjectId
from config import jobs_collection, users_collection

# Job-related routes
def route_create_job():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('route_login'))
    
    assigned_to = request.form.get('assigned_to')
    # Set to None if empty string
    if not assigned_to:
        assigned_to = None
    
    # Set current time
    current_time = datetime.now()

    job_data = {
        'job_id': request.form.get('job_id'),
        'load_from': request.form.get('load_from'),
        'load_to': request.form.get('load_to'),
        'load_details': request.form.get('load_details'),
        'deadline': datetime.strptime(request.form.get('deadline'), '%Y-%m-%dT%H:%M') if request.form.get('deadline') else None,
        'status': 'assigned' if assigned_to else 'open',
        'created_by': session['username'],
        'created_at': current_time,
        'updated_at': current_time,  # Initially same as created_at
        'assigned_to': assigned_to
    }

    jobs_collection.insert_one(job_data)
    flash('Job created successfully!', 'success')
    return redirect(url_for('route_admin_dashboard'))

def route_assign_job(job_id):
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('route_login'))

    username = request.form.get('username')
    current_user = session['username']
    
    # If no specific username provided, assign to current user (self-assignment)
    if not username:
        username = current_user
    
    # Verify this is a valid job that can be assigned
    job = jobs_collection.find_one({'_id': ObjectId(job_id)})
    if not job:
        flash('Job not found', 'danger')
        return redirect(url_for('route_home'))
    
    if job.get('assigned_to'):
        flash('This job is already assigned', 'warning')
        return redirect(url_for('route_home'))

    result = jobs_collection.update_one(
        {'_id': ObjectId(job_id)},
        {'$set': {
            'assigned_to': username,
            'status': 'assigned'
        }}
    )

    if result.modified_count > 0:
        flash('Job assigned successfully!', 'success')
    else:
        flash('Job assignment failed', 'danger')
    
    # Redirect back to wherever they came from (admin or user)
    user = users_collection.find_one({'username': current_user})
    is_admin = user.get('is_admin', False) if user else False
    
    if is_admin:
        return redirect(url_for('route_admin_dashboard'))
    return redirect(url_for('route_home'))

def route_update_job_status(job_id):
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('route_login'))

    status = request.form.get('status')
    
    # Only assigned users or admins can update job status
    job = jobs_collection.find_one({'_id': ObjectId(job_id)})
    if not job:
        flash('Job not found', 'danger')
        return redirect(url_for('route_home'))
        
    user = users_collection.find_one({'username': session['username']})
    is_admin = user.get('is_admin', False) if user else False
    
    if job['assigned_to'] != session['username'] and not is_admin:
        flash('You are not authorized to update this job', 'danger')
        return redirect(url_for('route_home'))
    
    # Add update timestamp and who updated it
    update_data = {
        'status': status,
        'updated_at': datetime.now(),
        'updated_by': session['username']
    }
    
    # If status is completed, record the completion time
    if status == 'completed':
        update_data['completed_at'] = datetime.now()
    
    result = jobs_collection.update_one(
        {'_id': ObjectId(job_id)},
        {'$set': update_data}
    )
    
    if result.modified_count > 0:
        flash('Job status updated successfully!', 'success')
    else:
        flash('Failed to update job status', 'danger')
    
    if is_admin:
        return redirect(url_for('route_admin_dashboard'))
    return redirect(url_for('route_home'))

def route_delete_job(job_id):
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('route_login'))

    result = jobs_collection.delete_one({'_id': ObjectId(job_id)})
    
    if result.deleted_count > 0:
        flash('Job deleted successfully!', 'success')
    else:
        flash('Job not found', 'danger')
    
    return redirect(url_for('route_admin_dashboard'))

# Additional helper functions for jobs
def get_jobs_by_status(status):
    return list(jobs_collection.find({'status': status}))

def get_job_by_id(job_id):
    return jobs_collection.find_one({'_id': ObjectId(job_id)})

def get_user_jobs(username):
    return list(jobs_collection.find({
        '$or': [
            {'assigned_to': username},
            {'created_by': username}
        ]
    }))