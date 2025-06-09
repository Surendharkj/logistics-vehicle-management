from flask import session, redirect, url_for, request, jsonify
from datetime import datetime
from config import users_collection, rates_collection, vehicles_collection

def checkin():
    if 'username' not in session:
        return redirect(url_for('route_login'))
    
    try:
        vehicle_number = request.form['vehicle_number'].upper()
        payment_mode = request.form['payment_mode']
        handler_username = session['username']
        
        # Get the user and their rate
        user = users_collection.find_one({'username': handler_username})
        if not user:
            return jsonify({
                'error': True,
                'message': 'User not found!'
            })
            
        rate = rates_collection.find_one({'_id': user['rate_id']})
        if not rate:
            return jsonify({
                'error': True,
                'message': 'Rate configuration not found!'
            })
        
        # Check if vehicle is already checked in by ANY user
        existing_vehicle = vehicles_collection.find_one({
            'vehicle_number': vehicle_number,
            'checkout_time': None
        })
        
        if existing_vehicle:
            return jsonify({
                'error': True,
                'message': f'Vehicle {vehicle_number} is already checked in by {existing_vehicle["handled_by"]}!'
            })
        
        # Create new check-in record
        checkin_time = datetime.now()
        vehicles_collection.insert_one({
            'vehicle_number': vehicle_number,
            'checkin_time': checkin_time,
            'checkout_time': None,
            'payment_mode': payment_mode,
            'handled_by': handler_username,
            'rate_id': rate['_id']
        })
        
        # Updated receipt HTML format
        receipt_html = f'''
        <div class="receipt-container" id="checkinReceipt">
            <div class="receipt">
                <div class="receipt-header">
                    <div class="company-logo">🅿️</div>
                    <h2>CHECKIN PAYROLL</h2>
                    <div class="receipt-meta">
                        #{vehicle_number}
                    </div>
                </div>
                
                <div class="receipt-divider"></div>
                
                <div class="receipt-body">
                    <div class="receipt-section">
                        <div class="receipt-row">
                            <span class="label">Check In:</span>
                            <span class="value">{checkin_time.strftime('%H:%M %d/%m/%y')}</span>
                        </div>
                        <div class="receipt-row">
                            <span class="label">Initial Rate:</span>
                            <span class="value">₹{rate['initial_amount']}</span>
                        </div>
                        <div class="receipt-row">
                            <span class="label">Duration:</span>
                            <span class="value">{rate['initial_duration']}h</span>
                        </div>
                    </div>
                    
                    <div class="receipt-divider"></div>
                    
                    <div class="receipt-section">
                        <div class="receipt-row">
                            <span class="label">Payment:</span>
                            <span class="value highlight">{payment_mode}</span>
                        </div>
                        <div class="receipt-row">
                            <span class="label">Staff ID:</span>
                            <span class="value">{handler_username}</span>
                        </div>
                    </div>
                </div>
                
                <div class="receipt-divider"></div>
                
                <div class="receipt-footer">
                    <div class="extra-info">
                        <small>Extra charges after {rate['initial_duration']}h</small>
                        <small>₹{rate['extra_charge']} per {rate['extra_charge_duration']}h</small>
                    </div>
                    <div class="thank-you">Thank You!</div>
                    <div class="barcode">IIIIIIIIIIII</div>
                </div>
            </div>
        </div>
        '''
        
        return jsonify({
            'success': True,
            'message': f'Vehicle {vehicle_number} has been successfully checked in!',
            'receipt': receipt_html
        })
                            
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error during check-in: {str(e)}'
        }) 