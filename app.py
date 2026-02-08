#!/usr/bin/env python3
"""
44 Physiques Check-In Server
Handles form submissions and file uploads for athlete check-ins
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template_string, redirect, session
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key = '44physiques_secret_key_2026'

# Simple auth for David
AUTH_USERNAME = 'DavidFenty44'
AUTH_PASSWORD = '44Physiques'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('/dashboard/login')
        return f(*args, **kwargs)
    return decorated_function

# Configuration
UPLOAD_FOLDER = Path("uploads")
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
UPLOAD_FOLDER.mkdir(exist_ok=True)


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def sanitize_folder_name(name):
    """Convert name to safe folder name"""
    safe = re.sub(r'[^\w\s-]', '', name)
    safe = safe.replace(' ', '_')
    safe = re.sub(r'_+', '_', safe)
    return safe.lower().strip('_')


def save_uploaded_file(file, athlete_folder, prefix):
    """Save uploaded file and return path info"""
    if file and file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.{ext}"
        filename = secure_filename(filename)
        
        file_path = athlete_folder / filename
        file.save(file_path)
        return str(file_path)
    return None


@app.route('/')
def index():
    """Serve the check-in form"""
    return send_from_directory('.', 'index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (logo, etc.)"""
    return send_from_directory('static', filename)


@app.route('/submit-checkin', methods=['POST'])
def submit_checkin():
    """Handle check-in form submission"""
    try:
        # Get form data
        client_name = request.form.get('client_name', '').strip()
        checkin_date = request.form.get('checkin_date', '').strip()
        
        if not client_name or not checkin_date:
            return jsonify({'error': 'Client name and check-in date are required'}), 400
        
        # Create athlete folder structure
        athlete_folder_name = sanitize_folder_name(client_name)
        date_folder = checkin_date.replace('-', '')
        athlete_folder = UPLOAD_FOLDER / athlete_folder_name / date_folder
        athlete_folder.mkdir(parents=True, exist_ok=True)
        
        # Collect all form data
        check_in_data = {
            'timestamp': datetime.now().isoformat(),
            'athlete_name': client_name,
            'checkin_date': checkin_date,
            'division': request.form.get('division', ''),
            'weight': request.form.get('weight', ''),
            'waist': request.form.get('waist', ''),
            'meals_compliant': request.form.get('meals_compliant', ''),
            'off_plan_foods': request.form.get('off_plan_foods', ''),
            'water_intake': request.form.get('water_intake', ''),
            'hunger': request.form.get('hunger', ''),
            'cravings': request.form.get('cravings', ''),
            'weight_workouts': request.form.get('weight_workouts', ''),
            'cardio_sessions': request.form.get('cardio_sessions', ''),
            'strength_trend': request.form.get('strength_trend', ''),
            'training_notes': request.form.get('training_notes', ''),
            'sleep_hours': request.form.get('sleep_hours', ''),
            'sleep_quality': request.form.get('sleep_quality', ''),
            'energy': request.form.get('energy', ''),
            'stress_level': request.form.get('stress_level', ''),
            'mood': request.form.get('mood', ''),
            'digestion': request.form.get('digestion', ''),
            'regularity': request.form.get('regularity', ''),
            'coach_notes': request.form.get('coach_notes', ''),
            'files': {}
        }
        
        # Handle all file uploads
        files_uploaded = []
        
        # Define all possible pose uploads
        all_pose_fields = [
            # Relaxed poses
            ('pose_front_relaxed', 'front_relaxed'),
            ('pose_left_relaxed', 'left_relaxed'),
            ('pose_right_relaxed', 'right_relaxed'),
            ('pose_rear_relaxed', 'rear_relaxed'),
            # Bikini poses
            ('bikini_front', 'bikini_front'),
            ('bikini_left', 'bikini_left'),
            ('bikini_rear', 'bikini_rear'),
            ('bikini_right', 'bikini_right'),
            # Figure poses
            ('figure_front', 'figure_front'),
            ('figure_left', 'figure_left'),
            ('figure_rear', 'figure_rear'),
            ('figure_right', 'figure_right'),
            # Wellness poses
            ('wellness_front', 'wellness_front'),
            ('wellness_left', 'wellness_left'),
            ('wellness_rear', 'wellness_rear'),
            ('wellness_right', 'wellness_right'),
            # Women's Physique poses
            ('wp_front', 'wp_front'),
            ('wp_left', 'wp_left'),
            ('wp_rear', 'wp_rear'),
            ('wp_right', 'wp_right'),
            ('wp_front_db', 'wp_front_db'),
            ('wp_side_chest', 'wp_side_chest'),
            ('wp_rear_db', 'wp_rear_db'),
            ('wp_side_tri', 'wp_side_tri'),
            ('wp_abs', 'wp_abs'),
            # Men's Physique
            ('mp_front', 'mp_front'),
            ('mp_back', 'mp_back'),
            # Bodybuilding poses
            ('bb_front_db', 'bb_front_db'),
            ('bb_front_lat', 'bb_front_lat'),
            ('bb_side_chest', 'bb_side_chest'),
            ('bb_back_db', 'bb_back_db'),
            ('bb_back_lat', 'bb_back_lat'),
            ('bb_side_tri', 'bb_side_tri'),
            ('bb_abs', 'bb_abs'),
            # Classic Physique
            ('classic_front_db', 'classic_front_db'),
            ('classic_side_chest', 'classic_side_chest'),
            ('classic_rear_db', 'classic_rear_db'),
            ('classic_abs', 'classic_abs'),
            ('classic_favorite', 'classic_favorite'),
            # Video
            ('posing_video', 'posing_video')
        ]
        
        for field_name, file_prefix in all_pose_fields:
            if field_name in request.files:
                file_path = save_uploaded_file(request.files[field_name], athlete_folder, file_prefix)
                if file_path:
                    check_in_data['files'][field_name] = file_path
                    files_uploaded.append(file_prefix)
        
        # Save check-in data
        data_file = UPLOAD_FOLDER / f"{athlete_folder_name}_checkins.json"
        all_checkins = []
        if data_file.exists():
            with open(data_file, 'r') as f:
                all_checkins = json.load(f)
        
        all_checkins.append(check_in_data)
        
        with open(data_file, 'w') as f:
            json.dump(all_checkins, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Check-in submitted successfully!',
            'athlete': client_name,
            'checkin_date': checkin_date,
            'files_uploaded': len(files_uploaded)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/dashboard/login', methods=['GET', 'POST'])
def dashboard_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == AUTH_USERNAME and password == AUTH_PASSWORD:
            session['logged_in'] = True
            return redirect('/dashboard')
        return '<h1 style="color: #791619; text-align: center; margin-top: 100px;">Invalid credentials. <a href="/dashboard/login">Try again</a></h1>'
    
    return '''<!DOCTYPE html>
<html>
<head>
    <title>Coach Login - 44 Physiques</title>
    <style>
        body { background: #0a0a0a; color: #fff; font-family: Inter, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .login-box { background: #111; border: 2px solid #791619; padding: 40px; border-radius: 12px; width: 100%; max-width: 400px; }
        h1 { color: #791619; text-align: center; margin-bottom: 30px; font-family: Bebas Neue, sans-serif; letter-spacing: 3px; }
        input { width: 100%; padding: 12px; margin-bottom: 15px; background: #1a1a1a; border: 2px solid #333; border-radius: 6px; color: #fff; font-size: 1rem; }
        button { width: 100%; padding: 15px; background: #791619; color: #fff; border: none; border-radius: 6px; font-size: 1.1rem; font-weight: 600; cursor: pointer; }
        button:hover { background: #8a1a1d; }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>44 PHYSIQUES<br>COACH LOGIN</h1>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">LOGIN</button>
        </form>
    </div>
</body>
</html>'''

@app.route('/dashboard/logout')
def dashboard_logout():
    session.pop('logged_in', None)
    return redirect('/dashboard/login')

@app.route('/dashboard')
@login_required
def dashboard():
    # Read all check-in data
    checkins = []
    total_checkins = 0
    new_checkins = 0
    needs_attention = 0
    total_energy = 0
    
    if UPLOAD_FOLDER.exists():
        for json_file in UPLOAD_FOLDER.glob('*_checkins.json'):
            with open(json_file, 'r') as f:
                data = json.load(f)
                for checkin in data:
                    total_checkins += 1
                    # Get photos
                    photos = []
                    if 'files' in checkin:
                        for key, path in checkin['files'].items():
                            if not key.endswith('video'):
                                photos.append(f'/uploads/{path}')
                    
                    # Determine status
                    status = 'new'
                    if checkin.get('meals_compliant', '100') not in ['', '100'] and int(checkin.get('meals_compliant', 100)) < 80:
                        status = 'needs-attention'
                        needs_attention += 1
                    
                    if checkin.get('energy'):
                        try:
                            total_energy += int(checkin['energy'])
                        except:
                            pass
                    
                    checkins.append({
                        'id': f"{checkin['athlete_name']}_{checkin['timestamp']}",
                        'athlete_name': checkin['athlete_name'],
                        'checkin_date': checkin['checkin_date'],
                        'division': checkin.get('division', ''),
                        'weight': checkin.get('weight', 'N/A'),
                        'waist': checkin.get('waist', 'N/A'),
                        'meals_compliant': checkin.get('meals_compliant', 'N/A'),
                        'energy': checkin.get('energy', 'N/A'),
                        'weight_workouts': checkin.get('weight_workouts', '0'),
                        'cardio_sessions': checkin.get('cardio_sessions', '0'),
                        'status': status,
                        'photos': photos[:4]  # Show first 4 photos
                    })
    
    # Sort by date (newest first)
    checkins.sort(key=lambda x: x['checkin_date'], reverse=True)
    new_checkins = len([c for c in checkins if c['status'] == 'new'])
    avg_energy = round(total_energy / len(checkins), 1) if checkins else 0
    
    # Read template
    template_path = Path(__file__).parent / 'templates' / 'dashboard.html'
    if template_path.exists():
        with open(template_path, 'r') as f:
            template = f.read()
    else:
        return '<h1>Dashboard template not found</h1>'
    
    # Simple template rendering
    html = template.replace('{{ total_checkins }}', str(total_checkins))
    html = html.replace('{{ new_checkins }}', str(new_checkins))
    html = html.replace('{{ needs_attention }}', str(needs_attention))
    html = html.replace('{{ avg_energy }}', str(avg_energy))
    
    # Render checkin cards
    checkin_html = ''
    for checkin in checkins:
        photos_html = ''
        for photo in checkin['photos']:
            photos_html += f'<img src="{photo}" class="photo-thumb" onclick="openLightbox(\'{photo}\')">'
        
        checkin_html += f'''
        <div class="athlete-card {checkin['status']}" data-status="{checkin['status']}" data-division="{checkin['division']}">
            <div class="athlete-header">
                <div>
                    <div class="athlete-name">{checkin['athlete_name']}</div>
                    <div class="checkin-date">{checkin['checkin_date']}</div>
                </div>
                <span class="status-badge status-{checkin['status']}">{checkin['status']}</span>
            </div>
            <div class="metrics-grid">
                <div class="metric"><div class="metric-label">Weight</div><div class="metric-value">{checkin['weight']} lbs</div></div>
                <div class="metric"><div class="metric-label">Waist</div><div class="metric-value">{checkin['waist']}"</div></div>
                <div class="metric"><div class="metric-label">Meal Compliance</div><div class="metric-value {'warning' if checkin['meals_compliant'] not in ['N/A', '100'] and int(checkin['meals_compliant']) < 80 else 'good'}">{checkin['meals_compliant']}%</div></div>
                <div class="metric"><div class="metric-label">Energy Level</div><div class="metric-value">{checkin['energy']}/10</div></div>
                <div class="metric"><div class="metric-label">Training</div><div class="metric-value">{checkin['weight_workouts']} workouts</div></div>
                <div class="metric"><div class="metric-label">Cardio</div><div class="metric-value">{checkin['cardio_sessions']} sessions</div></div>
            </div>
            {"<div class='photos-section'><div class='photos-label'>Photos</div><div class='photos-grid'>" + photos_html + "</div></div>" if photos_html else ""}
        </div>
        '''
    
    html = html.replace('{% for checkin in checkins %}', '')
    html = html.replace('{% endfor %}', '')
    html = html.replace('{{ checkin.athlete_name }}', '')
    html = html.replace('{% if not checkins %}', '')
    html = html.replace('{% endif %}', '')
    html = html.replace('{% for photo in checkin.photos %}', '')
    
    # Insert checkin cards
    if checkins:
        html = html.replace('<div class="athlete-grid" id="checkinGrid">', f'<div class="athlete-grid" id="checkinGrid">{checkin_html}')
    
    return render_template_string(html)

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)