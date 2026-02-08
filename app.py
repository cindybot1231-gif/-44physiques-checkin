#!/usr/bin/env python3
"""
44 Physiques Check-In Server with PostgreSQL
Handles form submissions and file uploads for athlete check-ins
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, redirect, session
from werkzeug.utils import secure_filename
from functools import wraps
import psycopg2
from urllib.parse import urlparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', '44physiques_secret_key_2026')

# Simple auth for David
AUTH_USERNAME = 'DavidFenty44'
AUTH_PASSWORD = '44Physiques'

# Database setup
def get_db_connection():
    """Get PostgreSQL connection from environment"""
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Render provides DATABASE_URL
        result = urlparse(database_url)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
    else:
        # Local development - use SQLite fallback
        import sqlite3
        conn = sqlite3.connect('checkins.db')
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if PostgreSQL or SQLite
    is_postgres = hasattr(conn, 'server_version')
    
    if is_postgres:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS checkins (
                id SERIAL PRIMARY KEY,
                athlete_name VARCHAR(255) NOT NULL,
                checkin_date DATE NOT NULL,
                division VARCHAR(100),
                weight VARCHAR(50),
                waist VARCHAR(50),
                meals_compliant VARCHAR(50),
                off_plan_foods TEXT,
                water_intake VARCHAR(50),
                hunger VARCHAR(50),
                cravings TEXT,
                weight_workouts VARCHAR(50),
                cardio_sessions VARCHAR(50),
                strength_trend VARCHAR(100),
                training_notes TEXT,
                sleep_hours VARCHAR(50),
                sleep_quality VARCHAR(50),
                energy VARCHAR(50),
                stress_level VARCHAR(50),
                mood VARCHAR(100),
                digestion VARCHAR(100),
                regularity VARCHAR(100),
                coach_notes TEXT,
                photos JSONB DEFAULT '[]',
                video_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'new'
            )
        ''')
    else:
        # SQLite version
        cur.execute('''
            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                athlete_name TEXT NOT NULL,
                checkin_date TEXT NOT NULL,
                division TEXT,
                weight TEXT,
                waist TEXT,
                meals_compliant TEXT,
                off_plan_foods TEXT,
                water_intake TEXT,
                hunger TEXT,
                cravings TEXT,
                weight_workouts TEXT,
                cardio_sessions TEXT,
                strength_trend TEXT,
                training_notes TEXT,
                sleep_hours TEXT,
                sleep_quality TEXT,
                energy TEXT,
                stress_level TEXT,
                mood TEXT,
                digestion TEXT,
                regularity TEXT,
                coach_notes TEXT,
                photos TEXT DEFAULT '[]',
                video_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'new'
            )
        ''')
    
    conn.commit()
    cur.close()
    conn.close()

# Initialize DB on startup
init_db()

# File upload config
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('/dashboard/login')
        return f(*args, **kwargs)
    return decorated_function

def send_checkin_email(checkin_data, photos, video_path):
    """Send email notification to David when athlete submits check-in using Outlook SMTP"""
    import threading
    
    def send_email_async():
        try:
            # Get credentials from environment
            smtp_user = os.environ.get('SMTP_USER', 'cindybot123125@outlook.com')
            smtp_pass = os.environ.get('SMTP_PASSWORD', '')
            coach_email = os.environ.get('COACH_EMAIL', 'david@44physiques.com')
            
            if not smtp_pass:
                print("SMTP password not configured - skipping email")
                return
            
            # Build email content
            subject = f"New Check-in: {checkin_data['athlete_name']} - {checkin_data['checkin_date']}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background: #0a0a0a; color: #fff; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #111; border: 2px solid #791619; border-radius: 12px; padding: 30px;">
                    <h1 style="color: #791619; text-align: center; margin-bottom: 30px;">44 PHYSIQUES</h1>
                    <h2 style="color: #fff; border-bottom: 2px solid #791619; padding-bottom: 10px;">New Athlete Check-in</h2>
                    
                    <div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #791619; margin-bottom: 15px;">Athlete Information</h3>
                        <p><strong>Name:</strong> {checkin_data['athlete_name']}</p>
                        <p><strong>Date:</strong> {checkin_data['checkin_date']}</p>
                        <p><strong>Division:</strong> {checkin_data.get('division', 'N/A')}</p>
                    </div>
                    
                    <div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #791619; margin-bottom: 15px;">Body Stats</h3>
                        <p><strong>Weight:</strong> {checkin_data.get('weight', 'N/A')} lbs</p>
                        <p><strong>Waist:</strong> {checkin_data.get('waist', 'N/A')}"</p>
                    </div>
                    
                    <div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #791619; margin-bottom: 15px;">Nutrition & Training</h3>
                        <p><strong>Meal Compliance:</strong> {checkin_data.get('meals_compliant', 'N/A')}%</p>
                        <p><strong>Water Intake:</strong> {checkin_data.get('water_intake', 'N/A')} gallons</p>
                        <p><strong>Hunger Level:</strong> {checkin_data.get('hunger', 'N/A')}/10</p>
                        <p><strong>Weight Workouts:</strong> {checkin_data.get('weight_workouts', '0')}</p>
                        <p><strong>Cardio Sessions:</strong> {checkin_data.get('cardio_sessions', '0')}</p>
                        <p><strong>Strength Trend:</strong> {checkin_data.get('strength_trend', 'N/A')}</p>
                    </div>
                    
                    <div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #791619; margin-bottom: 15px;">Recovery</h3>
                        <p><strong>Sleep:</strong> {checkin_data.get('sleep_hours', 'N/A')} hours ({checkin_data.get('sleep_quality', 'N/A')})</p>
                        <p><strong>Energy Level:</strong> {checkin_data.get('energy', 'N/A')}/10</p>
                        <p><strong>Stress Level:</strong> {checkin_data.get('stress_level', 'N/A')}</p>
                        <p><strong>Mood:</strong> {checkin_data.get('mood', 'N/A')}</p>
                    </div>
                    
                    <div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #791619; margin-bottom: 15px;">Digestion</h3>
                        <p><strong>Bloating/GI:</strong> {checkin_data.get('digestion', 'N/A')}</p>
                        <p><strong>Regularity:</strong> {checkin_data.get('regularity', 'N/A')}</p>
                    </div>
                    
                    <div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #791619; margin-bottom: 15px;">Files</h3>
                        <p><strong>Photos Uploaded:</strong> {len(photos)}</p>
                        <p><strong>Video Uploaded:</strong> {'Yes' if video_path else 'No'}</p>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px; padding: 20px; background: #791619; border-radius: 8px;">
                        <a href="https://44physiques-checkin.onrender.com/dashboard" style="color: #fff; text-decoration: none; font-weight: bold; font-size: 1.1rem;">VIEW FULL CHECK-IN IN DASHBOARD</a>
                    </div>
                    
                    <p style="text-align: center; color: #888; margin-top: 30px; font-size: 0.9rem;">
                        44 Physiques Coaching System<br>
                        "Chase the Physique"
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = coach_email
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send via Outlook SMTP
            server = smtplib.SMTP('smtp.office365.com', 587)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, coach_email, msg.as_string())
            server.quit()
            
            print(f"Email sent to {coach_email} via Outlook")
            
        except Exception as e:
            print(f"Error sending email: {e}")
    
    # Start email in background thread
    email_thread = threading.Thread(target=send_email_async)
    email_thread.daemon = True
    email_thread.start()


def sanitize_folder_name(name):
        subject = f"New Check-in: {checkin_data['athlete_name']} - {checkin_data['checkin_date']}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #0a0a0a; color: #fff; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #111; border: 2px solid #791619; border-radius: 12px; padding: 30px;">
                <h1 style="color: #791619; text-align: center; margin-bottom: 30px;">44 PHYSIQUES</h1>
                <h2 style="color: #fff; border-bottom: 2px solid #791619; padding-bottom: 10px;">New Athlete Check-in</h2>
                
                <div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #791619; margin-bottom: 15px;">Athlete Information</h3>
                    <p><strong>Name:</strong> {checkin_data['athlete_name']}</p>
                    <p><strong>Date:</strong> {checkin_data['checkin_date']}</p>
                    <p><strong>Division:</strong> {checkin_data.get('division', 'N/A')}</p>
                </div>
                
                <div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #791619; margin-bottom: 15px;">Body Stats</h3>
                    <p><strong>Weight:</strong> {checkin_data.get('weight', 'N/A')} lbs</p>
                    <p><strong>Waist:</strong> {checkin_data.get('waist', 'N/A')}"</p>
                </div>
                
                <div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #791619; margin-bottom: 15px;">Nutrition & Training</h3>
                    <p><strong>Meal Compliance:</strong> {checkin_data.get('meals_compliant', 'N/A')}%</p>
                    <p><strong>Water Intake:</strong> {checkin_data.get('water_intake', 'N/A')} gallons</p>
                    <p><strong>Hunger Level:</strong> {checkin_data.get('hunger', 'N/A')}/10</p>
                    <p><strong>Weight Workouts:</strong> {checkin_data.get('weight_workouts', '0')}</p>
                    <p><strong>Cardio Sessions:</strong> {checkin_data.get('cardio_sessions', '0')}</p>
                    <p><strong>Strength Trend:</strong> {checkin_data.get('strength_trend', 'N/A')}</p>
                </div>
                
                <div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #791619; margin-bottom: 15px;">Recovery</h3>
                    <p><strong>Sleep:</strong> {checkin_data.get('sleep_hours', 'N/A')} hours ({checkin_data.get('sleep_quality', 'N/A')})</p>
                    <p><strong>Energy Level:</strong> {checkin_data.get('energy', 'N/A')}/10</p>
                    <p><strong>Stress Level:</strong> {checkin_data.get('stress_level', 'N/A')}</p>
                    <p><strong>Mood:</strong> {checkin_data.get('mood', 'N/A')}</p>
                </div>
                
                <div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #791619; margin-bottom: 15px;">Digestion</h3>
                    <p><strong>Bloating/GI:</strong> {checkin_data.get('digestion', 'N/A')}</p>
                    <p><strong>Regularity:</strong> {checkin_data.get('regularity', 'N/A')}</p>
                </div>
                
                {f'<div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;"><h3 style="color: #791619; margin-bottom: 15px;">Off-Plan Foods</h3><p>{checkin_data.get("off_plan_foods", "None")}</p></div>' if checkin_data.get('off_plan_foods') else ''}
                
                {f'<div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;"><h3 style="color: #791619; margin-bottom: 15px;">Coach Notes</h3><p>{checkin_data.get("coach_notes", "None")}</p></div>' if checkin_data.get('coach_notes') else ''}
                
                <div style="background: #1a1a1a; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #791619; margin-bottom: 15px;">Files</h3>
                    <p><strong>Photos Uploaded:</strong> {len(photos)}</p>
                    <p><strong>Video Uploaded:</strong> {'Yes' if video_path else 'No'}</p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding: 20px; background: #791619; border-radius: 8px;">
                    <a href="https://44physiques-checkin.onrender.com/dashboard" style="color: #fff; text-decoration: none; font-weight: bold; font-size: 1.1rem;">VIEW FULL CHECK-IN IN DASHBOARD</a>
                </div>
                
                <p style="text-align: center; color: #888; margin-top: 30px; font-size: 0.9rem;">
                    44 Physiques Coaching System<br>
                    "Chase the Physique"
                </p>
            </div>
        </body>
        </html>
        """
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = coach_email
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send via Outlook SMTP
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, coach_email, msg.as_string())
        server.quit()
        
}
    """Convert name to safe folder name"""
    safe = re.sub(r'[^\w\s-]', '', name)
    safe = safe.replace(' ', '_')
    safe = re.sub(r'_+', '_', safe)
    return safe.lower().strip('_')

def save_uploaded_file(file, athlete_folder, prefix):
    """Save uploaded file and return path"""
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
    return send_from_directory('static', filename)

@app.route('/submit-checkin', methods=['POST'])
def submit_checkin():
    """Handle check-in form submission"""
    try:
        client_name = request.form.get('client_name', '').strip()
        checkin_date = request.form.get('checkin_date', '').strip()
        
        if not client_name or not checkin_date:
            return jsonify({'error': 'Client name and check-in date are required'}), 400
        
        # Create athlete folder
        athlete_folder_name = sanitize_folder_name(client_name)
        date_folder = checkin_date.replace('-', '')
        athlete_folder = UPLOAD_FOLDER / athlete_folder_name / date_folder
        athlete_folder.mkdir(parents=True, exist_ok=True)
        
        # Collect photos
        photos = []
        video_path = None
        
        # All file fields
        file_fields = [
            ('pose_front_relaxed', 'front_relaxed'),
            ('pose_left_relaxed', 'left_relaxed'),
            ('pose_right_relaxed', 'right_relaxed'),
            ('pose_rear_relaxed', 'rear_relaxed'),
            ('bikini_front', 'bikini_front'), ('bikini_left', 'bikini_left'),
            ('bikini_rear', 'bikini_rear'), ('bikini_right', 'bikini_right'),
            ('figure_front', 'figure_front'), ('figure_left', 'figure_left'),
            ('figure_rear', 'figure_rear'), ('figure_right', 'figure_right'),
            ('wellness_front', 'wellness_front'), ('wellness_left', 'wellness_left'),
            ('wellness_rear', 'wellness_rear'), ('wellness_right', 'wellness_right'),
            ('wp_front', 'wp_front'), ('wp_left', 'wp_left'), ('wp_rear', 'wp_rear'), ('wp_right', 'wp_right'),
            ('wp_front_db', 'wp_front_db'), ('wp_side_chest', 'wp_side_chest'),
            ('wp_rear_db', 'wp_rear_db'), ('wp_side_tri', 'wp_side_tri'), ('wp_abs', 'wp_abs'),
            ('mp_front', 'mp_front'), ('mp_back', 'mp_back'),
            ('bb_front_db', 'bb_front_db'), ('bb_front_lat', 'bb_front_lat'),
            ('bb_side_chest', 'bb_side_chest'), ('bb_back_db', 'bb_back_db'),
            ('bb_back_lat', 'bb_back_lat'), ('bb_side_tri', 'bb_side_tri'), ('bb_abs', 'bb_abs'),
            ('classic_front_db', 'classic_front_db'), ('classic_side_chest', 'classic_side_chest'),
            ('classic_rear_db', 'classic_rear_db'), ('classic_abs', 'classic_abs'),
            ('classic_favorite', 'classic_favorite'),
            ('posing_video', 'posing_video')
        ]
        
        for field_name, file_prefix in file_fields:
            if field_name in request.files:
                file_path = save_uploaded_file(request.files[field_name], athlete_folder, file_prefix)
                if file_path:
                    if field_name == 'posing_video':
                        video_path = str(file_path)
                    else:
                        photos.append(str(file_path))
        
        # Determine status
        meals = request.form.get('meals_compliant', '100')
        status = 'new'
        if meals and meals not in ['', '100']:
            try:
                if int(meals) < 80:
                    status = 'needs-attention'
            except:
                pass
        
        # Prepare check-in data for email
        check_in_data = {
            'athlete_name': client_name,
            'checkin_date': checkin_date,
            'division': request.form.get('division', ''),
            'weight': request.form.get('weight', ''),
            'waist': request.form.get('waist', ''),
            'meals_compliant': meals,
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
            'coach_notes': request.form.get('coach_notes', '')
        }
        
        # Save to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if PostgreSQL (has server_version attribute)
        is_postgres = hasattr(conn, 'server_version')
        
        if is_postgres:
            cur.execute('''
                INSERT INTO checkins 
                (athlete_name, checkin_date, division, weight, waist, meals_compliant, 
                off_plan_foods, water_intake, hunger, cravings, weight_workouts, 
                cardio_sessions, strength_trend, training_notes, sleep_hours, sleep_quality,
                energy, stress_level, mood, digestion, regularity, coach_notes, photos, video_path, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                client_name, checkin_date, request.form.get('division', ''),
                request.form.get('weight', ''), request.form.get('waist', ''),
                meals, request.form.get('off_plan_foods', ''),
                request.form.get('water_intake', ''), request.form.get('hunger', ''),
                request.form.get('cravings', ''), request.form.get('weight_workouts', ''),
                request.form.get('cardio_sessions', ''), request.form.get('strength_trend', ''),
                request.form.get('training_notes', ''), request.form.get('sleep_hours', ''),
                request.form.get('sleep_quality', ''), request.form.get('energy', ''),
                request.form.get('stress_level', ''), request.form.get('mood', ''),
                request.form.get('digestion', ''), request.form.get('regularity', ''),
                request.form.get('coach_notes', ''), json.dumps(photos), video_path, status
            ))
        else:
            # SQLite
            cur.execute('''
                INSERT INTO checkins 
                (athlete_name, checkin_date, division, weight, waist, meals_compliant, 
                off_plan_foods, water_intake, hunger, cravings, weight_workouts, 
                cardio_sessions, strength_trend, training_notes, sleep_hours, sleep_quality,
                energy, stress_level, mood, digestion, regularity, coach_notes, photos, video_path, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_name, checkin_date, request.form.get('division', ''),
                request.form.get('weight', ''), request.form.get('waist', ''),
                meals, request.form.get('off_plan_foods', ''),
                request.form.get('water_intake', ''), request.form.get('hunger', ''),
                request.form.get('cravings', ''), request.form.get('weight_workouts', ''),
                request.form.get('cardio_sessions', ''), request.form.get('strength_trend', ''),
                request.form.get('training_notes', ''), request.form.get('sleep_hours', ''),
                request.form.get('sleep_quality', ''), request.form.get('energy', ''),
                request.form.get('stress_level', ''), request.form.get('mood', ''),
                request.form.get('digestion', ''), request.form.get('regularity', ''),
                request.form.get('coach_notes', ''), json.dumps(photos), video_path, status
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Send email notification to coach
        send_checkin_email(check_in_data, photos, video_path)
        
        return jsonify({
            'success': True,
            'message': 'Check-in submitted successfully!',
            'athlete': client_name,
            'files_uploaded': len(photos) + (1 if video_path else 0)
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
    # Get stats from database
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if PostgreSQL
    is_postgres = hasattr(conn, 'server_version')
    
    # Get counts
    if is_postgres:
        cur.execute("SELECT COUNT(*) FROM checkins")
        total_checkins = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM checkins WHERE status = 'new'")
        new_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM checkins WHERE status = 'needs-attention'")
        needs_attention = cur.fetchone()[0]
        
        # Get all checkins
        cur.execute('''
            SELECT athlete_name, checkin_date, division, weight, waist, meals_compliant,
                   energy, weight_workouts, cardio_sessions, status, photos
            FROM checkins ORDER BY created_at DESC
        ''')
        rows = cur.fetchall()
    else:
        # SQLite
        cur.execute("SELECT COUNT(*) FROM checkins")
        total_checkins = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM checkins WHERE status = 'new'")
        new_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM checkins WHERE status = 'needs-attention'")
        needs_attention = cur.fetchone()[0]
        
        cur.execute('''
            SELECT athlete_name, checkin_date, division, weight, waist, meals_compliant,
                   energy, weight_workouts, cardio_sessions, status, photos
            FROM checkins ORDER BY created_at DESC
        ''')
        rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Build cards HTML
    cards_html = ''
    for row in rows:
        athlete_name, checkin_date, division, weight, waist, meals_compliant, energy, weight_workouts, cardio_sessions, status, photos_json = row
        
        # Parse photos
        try:
            photos = json.loads(photos_json) if photos_json else []
        except:
            photos = []
        
        # Meal compliance class
        meal_class = 'good'
        if meals_compliant and meals_compliant not in ['N/A', '100']:
            try:
                if int(meals_compliant) < 80:
                    meal_class = 'warning'
            except:
                pass
        
        # Photos HTML
        photos_html = ''
        if photos:
            photos_html = "<div class='photos-section'><div class='photos-label'>Photos (" + str(len(photos)) + ")</div><div class='photos-grid'>"
            for p in photos:
                # Convert Windows path to URL path
                p_url = p.replace('\\', '/')
                photos_html += f'<img src="/uploads/{p_url}" class="photo-thumb" onclick="openLightbox(&#39;/uploads/{p_url}&#39;)">'
            photos_html += "</div></div>"
        
        cards_html += f'''
        <div class="athlete-card {status}" data-status="{status}" data-division="{division}">
            <div class="athlete-header">
                <div>
                    <div class="athlete-name">{athlete_name}</div>
                    <div class="checkin-date">{checkin_date}</div>
                </div>
                <span class="status-badge status-{status}">{status}</span>
            </div>
            <div class="metrics-grid">
                <div class="metric"><div class="metric-label">Weight</div><div class="metric-value">{weight or 'N/A'} lbs</div></div>
                <div class="metric"><div class="metric-label">Waist</div><div class="metric-value">{waist or 'N/A'}"</div></div>
                <div class="metric"><div class="metric-label">Meal Compliance</div><div class="metric-value {meal_class}">{meals_compliant or 'N/A'}%</div></div>
                <div class="metric"><div class="metric-label">Energy Level</div><div class="metric-value">{energy or 'N/A'}/10</div></div>
                <div class="metric"><div class="metric-label">Training</div><div class="metric-value">{weight_workouts or '0'} workouts</div></div>
                <div class="metric"><div class="metric-label">Cardio</div><div class="metric-value">{cardio_sessions or '0'} sessions</div></div>
            </div>
            {photos_html}
        </div>
        '''
    
    # Empty state
    if not rows:
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