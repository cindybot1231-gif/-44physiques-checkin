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
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)