"""
Sahayog - Advanced Waste Auditing Platform
Pure Auditing Focus - AI-Powered Waste Analysis
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key = 'sahayog-secret-key-2024'  # Change in production
app.config['APPLICATION_ROOT'] = '/flask'
app.config.setdefault('SESSION_COOKIE_PATH', '/flask')

# Configuration
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simple auditor credentials
VALID_AUDITORS = {
    'admin': 'audit123',
    'auditor': 'audit123',
    'analyst': 'audit123',
    'user': 'test123'
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def advanced_waste_analysis(image_path):
    """
    Advanced AI Waste Analysis Function
    Uses real computer vision to analyze images and classify waste
    """
    try:
        # Import the AI analyzer
        from ai_waste_analyzer import waste_analyzer
        
        # Perform real AI analysis
        result = waste_analyzer.analyze_image(image_path)
        
        # Add metadata
        result['image_file'] = os.path.basename(image_path)
        result['image_size'] = f"{os.path.getsize(image_path)} bytes"
        result['auditor'] = session.get('username', 'Unknown')
        
        return result
        
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        # Fallback to basic analysis
        return get_fallback_analysis(image_path)

def get_fallback_analysis(image_path):
    """Fallback analysis when AI fails"""
    return {
        'primary_type': 'UNKNOWN_WASTE',
        'confidence': 0.3,
        'sub_category': 'Mixed Waste',
        'recyclability': 'UNKNOWN',
        'environmental_impact': 'MEDIUM',
        'disposal_method': 'GENERAL_DISPOSAL',
        'processing_time': 'Unknown',
        'carbon_footprint': 'Unknown',
        'monetary_value': 'Unknown',
        'composition': {
            'mixed_materials': 100
        },
        'audit_score': 30,
        'segregation_quality': 'POOR',
        'contamination_level': 'HIGH',
        'recommendations': [
            'Manual inspection required',
            'Separate into different waste streams',
            'Consult waste management professional',
            'Check local recycling guidelines'
        ],
        'environmental_benefits': [
            'Proper sorting reduces environmental impact',
            'Prevents contamination of recycling streams'
        ],
        'processing_facilities': [
            'Local waste management facility',
            'Mixed waste processing center'
        ],
        'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'image_file': os.path.basename(image_path),
        'image_size': f"{os.path.getsize(image_path)} bytes",
        'auditor': session.get('username', 'Unknown'),
        'analysis_method': 'FALLBACK_DEFAULT'
    }

def require_login(f):
    """Decorator that ensures a guest session exists while skipping manual login."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            session['logged_in'] = True
            session['username'] = 'Guest Auditor'
        return f(*args, **kwargs)

    return decorated_function

# Routes
@app.route('/')
def index():
    """Landing page now goes straight to the dashboard."""

    session.setdefault('logged_in', True)
    session.setdefault('username', 'Guest Auditor')
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Legacy login route now auto-initializes a guest session and redirects."""

    session['logged_in'] = True
    session['username'] = request.form.get('username', 'Guest Auditor')
    flash('Welcome to the Auditing Platform', 'info')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Session cleared. Continuing as guest.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@require_login
def dashboard():
    """Main auditing dashboard"""
    return render_template('audit_dashboard.html', username=session.get('username', 'Auditor'))

@app.route('/audit', methods=['GET', 'POST'])
@require_login
def audit():
    """Advanced waste auditing page"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('audit'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('audit'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Perform advanced AI analysis
            flash('Image uploaded successfully! Performing advanced analysis...', 'success')
            
            # Simulate processing time
            import time
            time.sleep(3)
            
            # Get analysis results
            analysis_results = advanced_waste_analysis(filepath)
            
            # Store results in session for display
            session['last_analysis'] = analysis_results
            session['image_filename'] = filename
            
            return redirect(url_for('audit_results'))
        else:
            flash('Invalid file type. Please upload PNG, JPG, JPEG, or GIF', 'error')
            return redirect(url_for('audit'))
    
    return render_template('audit_upload.html', username=session.get('username', 'Auditor'))

@app.route('/results')
@require_login
def audit_results():
    """Display comprehensive audit results"""
    if 'last_analysis' not in session:
        flash('No analysis results found', 'error')
        return redirect(url_for('audit'))
    
    analysis = session['last_analysis']
    image_filename = session.get('image_filename', '')
    
    return render_template('audit_results_advanced.html', 
                         analysis=analysis, 
                         image_filename=image_filename,
                         username=session.get('username', 'Auditor'))

@app.route('/new-audit')
@require_login
def new_audit():
    """Start new audit"""
    session.pop('last_analysis', None)
    session.pop('image_filename', None)
    return redirect(url_for('audit'))

@app.route('/audit-history')
@require_login
def audit_history():
    """View audit history (simplified)"""
    # In a real application, this would fetch from database
    sample_history = [
        {
            'id': 1,
            'timestamp': '2025-10-12 16:30:00',
            'waste_type': 'ORGANIC_WASTE',
            'audit_score': 92,
            'status': 'COMPLETED'
        },
        {
            'id': 2,
            'timestamp': '2025-10-12 15:45:00',
            'waste_type': 'PLASTIC_WASTE',
            'audit_score': 78,
            'status': 'COMPLETED'
        },
        {
            'id': 3,
            'timestamp': '2025-10-12 14:20:00',
            'waste_type': 'ELECTRONIC_WASTE',
            'audit_score': 85,
            'status': 'COMPLETED'
        }
    ]
    
    return render_template('audit_history.html', 
                         history=sample_history,
                         username=session.get('username', 'Auditor'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
