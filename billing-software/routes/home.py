#now this my home.py backend file
from flask import session, redirect, url_for, render_template
from config import jobs_collection

def home():
    if 'username' not in session:
        return redirect(url_for('route_login'))
    
    username = session['username']
    
    # Get jobs assigned to this user
    user_jobs = list(jobs_collection.find({'assigned_to': username}))
    
    # Get available jobs (not assigned to anyone)
    available_jobs = list(jobs_collection.find({
        '$or': [
            {'assigned_to': None},
            {'assigned_to': ''}
        ],
        'status': 'open'
    }))
    
    print(f"Found {len(available_jobs)} available jobs")
    
    return render_template(
        'home.html', 
        username=username,
        user_jobs=user_jobs,
        available_jobs=available_jobs
    ) 