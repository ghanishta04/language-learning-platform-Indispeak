from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from app import db
from app.models import User, CompletedLesson, QuizScore
import os

profile_bp = Blueprint('profile', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_folder_path():
    """Return the absolute upload folder path, independent of the run directory."""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if os.path.isabs(upload_folder):
        return upload_folder
    project_root = os.path.dirname(current_app.root_path)
    return os.path.join(project_root, upload_folder)

@profile_bp.route('/user-profile')
@login_required
def user_profile():
    """User profile page"""
    user = current_user
    
    # Get user statistics
    completed_lessons = CompletedLesson.query.filter_by(user_id=user.id).count()
    quiz_scores = QuizScore.query.filter_by(user_id=user.id).all()
    
    total_attempts = len(quiz_scores)
    avg_score = 0
    if quiz_scores:
        avg_score = sum(score.score_percentage for score in quiz_scores) / total_attempts
    
    return render_template('profile.html',
                         user=user,
                         completed_lessons=completed_lessons,
                         total_attempts=total_attempts,
                         avg_score=avg_score)


@profile_bp.route('/user-settings')
@login_required
def user_settings():
    """User settings page"""
    return render_template('settings.html')


@profile_bp.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile_api():
    """Update user profile information"""
    user = current_user
    
    # Update name if provided
    name = request.form.get('name', '').strip()
    if name:
        user.name = name
    
    # Update bio if provided
    bio = request.form.get('bio', '').strip()
    if bio:
        user.bio = bio
    
    # Handle profile picture upload
    file = request.files.get('profile_pic')
    if file and file.filename:
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'Please upload a PNG, JPG, JPEG, or GIF image.'
            }), 400

        upload_dir = upload_folder_path()
        os.makedirs(upload_dir, exist_ok=True)

        # Remove old file if exists
        if user.profile_pic and user.profile_pic != 'default.png':
            old_path = os.path.join(upload_dir, user.profile_pic)
            if os.path.exists(old_path):
                os.remove(old_path)

        # Save new file
        filename = secure_filename(f"{user.id}_{datetime.utcnow().timestamp()}_{file.filename}")
        file.save(os.path.join(upload_dir, filename))
        user.profile_pic = filename
    
    user.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully',
        'profile_pic': user.profile_pic
    })


@profile_bp.route('/api/profile/change-password', methods=['POST'])
@login_required
def change_password_api():
    """Change user password"""
    user = current_user
    
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validate old password
    if not user.check_password(old_password):
        return jsonify({
            'success': False,
            'message': 'Current password is incorrect'
        }), 401
    
    # Validate new password
    if len(new_password) < 6:
        return jsonify({
            'success': False,
            'message': 'New password must be at least 6 characters'
        }), 400
    
    if new_password != confirm_password:
        return jsonify({
            'success': False,
            'message': 'New passwords do not match'
        }), 400
    
    # Update password
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Password changed successfully'
    })
