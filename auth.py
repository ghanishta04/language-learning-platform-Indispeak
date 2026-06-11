from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validation
        if not all([name, username, email, password]):
            return render_template('register.html', error='All fields are required'), 400
        
        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters'), 400
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match'), 400
        
        # Check if user exists
        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            return render_template('register.html', error='Username or Email already exists'), 400
        
        # Create new user
        user = User(name=name, username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Log user in after registration
            login_user(user)
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', error='Registration failed. Please try again.'), 500
    
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        login_input = request.form.get('login', '').strip()
        password = request.form.get('password', '').strip()
        
        if not login_input or not password:
            return render_template('login.html', error='Please provide email/username and password'), 400
        
        # Search by email or username
        user = User.query.filter(
            (User.email == login_input) | (User.username == login_input)
        ).first()
        
        if user and user.check_password(password):
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user)
            session['speak_word_of_day_on_dashboard'] = True
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            return render_template('login.html', error='Invalid email/username or password'), 401
    
    return render_template('login.html')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('auth.login'))
