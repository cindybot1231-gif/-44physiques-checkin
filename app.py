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
    new_count = 0
    needs_attention = 0
    total_energy = 0
    
    if UPLOAD_FOLDER.exists():
        for json_file in UPLOAD_FOLDER.glob('*_checkins.json'):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    for checkin in data:
                        total_checkins += 1
                        
                        # Determine status
                        status = 'new'
                        meals = checkin.get('meals_compliant', '100')
                        if meals and meals not in ['', '100']:
                            try:
                                if int(meals) < 80:
                                    status = 'needs-attention'
                                    needs_attention += 1
                            except:
                                pass
                        
                        if status == 'new':
                            new_count += 1
                        
                        # Get energy
                        energy = checkin.get('energy', '5')
                        try:
                            total_energy += int(energy)
                        except:
                            pass
                        
                        # Get photos
                        photos = []
                        if 'files' in checkin:
                            for key, path in checkin['files'].items():
                                if not key.endswith('video'):
                                    photos.append('/uploads/' + path.replace('\\', '/'))
                        
                        checkins.append({
                            'athlete_name': checkin.get('athlete_name', 'Unknown'),
                            'checkin_date': checkin.get('checkin_date', ''),
                            'division': checkin.get('division', ''),
                            'weight': checkin.get('weight', 'N/A'),
                            'waist': checkin.get('waist', 'N/A'),
                            'meals_compliant': meals if meals else 'N/A',
                            'energy': energy,
                            'weight_workouts': checkin.get('weight_workouts', '0'),
                            'cardio_sessions': checkin.get('cardio_sessions', '0'),
                            'status': status,
                            'photos': photos[:4]
                        })
            except Exception as e:
                print(f"Error reading {json_file}: {e}")
                continue
    
    # Sort by date (newest first)
    checkins.sort(key=lambda x: x['checkin_date'], reverse=True)
    avg_energy = round(total_energy / len(checkins), 1) if checkins else 0
    
    # Build HTML
    cards_html = ''
    for c in checkins:
        # Meal compliance class
        meal_class = 'good'
        if c['meals_compliant'] not in ['N/A', '100']:
            try:
                if int(c['meals_compliant']) < 80:
                    meal_class = 'warning'
            except:
                pass
        
        # Photos HTML
        photos_html = ''
        if c['photos']:
            photos_html = "<div class='photos-section'><div class='photos-label'>Photos (" + str(len(c['photos'])) + ")</div><div class='photos-grid'>"
            for p in c['photos']:
                photos_html += f'<img src="{p}" class="photo-thumb" onclick="openLightbox(&#39;{p}&#39;)">'
            photos_html += "</div></div>"
        
        cards_html += f'''
        <div class="athlete-card {c['status']}" data-status="{c['status']}" data-division="{c['division']}">
            <div class="athlete-header">
                <div>
                    <div class="athlete-name">{c['athlete_name']}</div>
                    <div class="checkin-date">{c['checkin_date']}</div>
                </div>
                <span class="status-badge status-{c['status']}">{c['status']}</span>
            </div>
            <div class="metrics-grid">
                <div class="metric"><div class="metric-label">Weight</div><div class="metric-value">{c['weight']} lbs</div></div>
                <div class="metric"><div class="metric-label">Waist</div><div class="metric-value">{c['waist']}"</div></div>
                <div class="metric"><div class="metric-label">Meal Compliance</div><div class="metric-value {meal_class}">{c['meals_compliant']}%</div></div>
                <div class="metric"><div class="metric-label">Energy Level</div><div class="metric-value">{c['energy']}/10</div></div>
                <div class="metric"><div class="metric-label">Training</div><div class="metric-value">{c['weight_workouts']} workouts</div></div>
                <div class="metric"><div class="metric-label">Cardio</div><div class="metric-value">{c['cardio_sessions']} sessions</div></div>
            </div>
            {photos_html}
        </div>
        '''
    
    # Empty state
    if not checkins:
        cards_html = '''
        <div class="empty-state">
            <div class="empty-state-icon">📋</div>
            <h2>No Check-ins Yet</h2>
            <p>Athlete check-ins will appear here once they start submitting.</p>
        </div>
        '''
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>44 Physiques - Coach Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #0a0a0a; color: #fff; line-height: 1.6; min-height: 100vh; }}
        .header {{ background: #1a1a1a; border-bottom: 4px solid #791619; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ font-family: 'Bebas Neue', sans-serif; font-size: 2rem; letter-spacing: 4px; color: #fff; }}
        .logo span {{ color: #791619; }}
        .logout-btn {{ background: transparent; border: 2px solid #791619; color: #791619; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; text-decoration: none; }}
        .logout-btn:hover {{ background: #791619; color: #fff; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 30px; }}
        .stats-bar {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #111; border: 1px solid #222; border-radius: 12px; padding: 20px; text-align: center; }}
        .stat-value {{ font-family: 'Bebas Neue', sans-serif; font-size: 3rem; color: #791619; }}
        .stat-label {{ color: #888; font-size: 0.9rem; margin-top: 5px; }}
        .athlete-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 20px; }}
        .athlete-card {{ background: #111; border: 1px solid #222; border-radius: 12px; padding: 20px; transition: all 0.3s ease; }}
        .athlete-card:hover {{ border-color: #791619; transform: translateY(-2px); }}
        .athlete-card.new {{ border-left: 4px solid #791619; }}
        .athlete-card.needs-attention {{ border-left: 4px solid #ff4444; }}
        .athlete-header {{ display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #333; }}
        .athlete-name {{ font-family: 'Bebas Neue', sans-serif; font-size: 1.5rem; color: #fff; }}
        .checkin-date {{ color: #888; font-size: 0.85rem; }}
        .status-badge {{ padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
        .status-new {{ background: rgba(121, 22, 25, 0.3); color: #791619; }}
        .status-needs-attention {{ background: rgba(255, 68, 68, 0.3); color: #ff4444; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 15px; }}
        .metric {{ background: #1a1a1a; padding: 10px; border-radius: 6px; }}
        .metric-label {{ font-size: 0.75rem; color: #888; text-transform: uppercase; }}
        .metric-value {{ font-size: 1.1rem; font-weight: 600; color: #fff; margin-top: 3px; }}
        .metric-value.warning {{ color: #ff4444; }}
        .metric-value.good {{ color: #2d8a2d; }}
        .photos-section {{ margin-top: 15px; }}
        .photos-label {{ font-size: 0.85rem; color: #888; margin-bottom: 10px; }}
        .photos-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 10px; }}
        .photo-thumb {{ width: 80px; height: 80px; object-fit: cover; border-radius: 6px; border: 2px solid #333; cursor: pointer; transition: all 0.2s; }}
        .photo-thumb:hover {{ border-color: #791619; transform: scale(1.05); }}
        .empty-state {{ text-align: center; padding: 60px; color: #888; grid-column: 1 / -1; }}
        .empty-state-icon {{ font-size: 4rem; margin-bottom: 20px; }}
        .lightbox {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 1000; justify-content: center; align-items: center; }}
        .lightbox img {{ max-width: 90%; max-height: 90%; object-fit: contain; }}
        .lightbox-close {{ position: absolute; top: 20px; right: 30px; font-size: 3rem; color: #fff; cursor: pointer; }}
        @media (max-width: 768px) {{ .athlete-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">44 <span>PHYSIQUES</span> COACH DASHBOARD</div>
        <a href="/dashboard/logout" class="logout-btn">Logout</a>
    </div>
    <div class="container">
        <div class="stats-bar">
            <div class="stat-card">
                <div class="stat-value">{total_checkins}</div>
                <div class="stat-label">Total Check-ins</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{new_count}</div>
                <div class="stat-label">New This Week</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{needs_attention}</div>
                <div class="stat-label">Need Attention</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{avg_energy}</div>
                <div class="stat-label">Avg Energy Level</div>
            </div>
        </div>
        <div class="athlete-grid">
            {cards_html}
        </div>
    </div>
    <div class="lightbox" id="lightbox" onclick="closeLightbox()">
        <span class="lightbox-close">&times;</span>
        <img id="lightbox-img" src="">
    </div>
    <script>
        function openLightbox(src) {{
            document.getElementById('lightbox-img').src = src;
            document.getElementById('lightbox').style.display = 'flex';
        }}
        function closeLightbox() {{
            document.getElementById('lightbox').style.display = 'none';
        }}
    </script>
</body>
</html>'''
    
    return html

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)