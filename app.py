from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
from datetime import datetime
import os

app = Flask(__name__)
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/submit-checkin', methods=['POST'])
def submit_checkin():
    try:
        client_name = request.form.get('client_name', '').strip()
        week_ending = request.form.get('week_ending', '').strip()
        
        if not client_name or not week_ending:
            return jsonify({'error': 'Name and week ending required'}), 400
        
        athlete_folder = UPLOAD_FOLDER / client_name.replace(' ', '_').lower() / week_ending.replace('-', '')
        athlete_folder.mkdir(parents=True, exist_ok=True)
        
        files_saved = []
        for key in request.files:
            file = request.files[key]
            if file.filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{key}_{timestamp}_{file.filename}"
                file.save(athlete_folder / filename)
                files_saved.append(key)
        
        return jsonify({
            'success': True,
            'message': 'Check-in saved!',
            'athlete': client_name,
            'files_saved': len(files_saved)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)