"""
Authentication routes for NEXAweb application
Handles login, logout, and admin setup functionality
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, SecurityLog
from database import get_mongo

auth_bp = Blueprint('auth', __name__, strict_slashes=False)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with rate limiting"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        print(f"🔐 Login attempt: {username}")
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('login.html')
        
        # Get client information for security logging
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        # Find user
        user_data = None
        if username:
            from models import User
            print(f"🔍 Looking for user: {username}")
            user_data = User.find_by_username(username)
            print(f"👤 User data found: {bool(user_data)}")
            if user_data:
                print(f"📋 User data keys: {list(user_data.keys())}")
                print(f"🔐 Stored password hash: {user_data.get('password_hash', 'Not found')}")
            else:
                print("❌ No user data returned")
                # Check if any users exist
                from database import get_mongo
                mongo = get_mongo()
                all_users = list(mongo.db.users.find())
                print(f"📊 Total users in database: {len(all_users)}")
                if all_users:
                    print(f"📝 Available usernames: {[user.get('username') for user in all_users]}")
                else:
                    print("❌ No users found in database")
        
        # Check credentials
        login_success = False
        if user_data:
            user = User(user_data)
            login_success = user.check_password(password)
            print(f"🔑 Password check result: {login_success}")
        else:
            print("❌ No user found with that username")
        
        # Log login attempt
        SecurityLog.create(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=login_success
        )
        
        # Send security notification for failed login attempts
        if not login_success:
            try:
                from utils.notifications import notify_security_alert
                telegram_success = notify_security_alert(username, ip_address, user_agent)
                if telegram_success:
                    print("✅ Security alert notification sent successfully")
                else:
                    print("❌ Failed to send security alert notification")
            except Exception as e:
                print(f"❌ Error sending security alert notification: {e}")
        
        if login_success:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.home'))


@auth_bp.route('/setup_admin', methods=['GET', 'POST'])
def setup_admin():
    """First-run admin setup - only works if no admin exists"""
    try:
        # Check if any admin users exist
        admin_count = User.count()
        
        if admin_count > 0:
            flash('Admin account already exists. Please login.', 'info')
            return redirect(url_for('auth.login'))
        
        if request.method == 'POST':
            # Double-check no admin exists
            current_count = User.count()
            if current_count > 0:
                return redirect(url_for('auth.login'))
            
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validation
            if not username or not password:
                flash('Username and password are required', 'error')
                return render_template('setup_admin.html')
            
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('setup_admin.html')
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return render_template('setup_admin.html')
            
            # Create admin user
            user_id = User.create_user(username, password)
            
            if user_id:
                flash('Admin account created successfully! You can now log in.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Error creating admin account', 'error')
        
        return render_template('setup_admin.html')
        
    except Exception as e:
        flash(f'Error during admin setup: {str(e)}', 'error')
        return render_template('setup_admin.html')


# User loader for Flask-Login
def load_user(user_id):
    """Load user from MongoDB using ObjectId"""
    try:
        user_data = User.find_by_id(user_id)
        if user_data:
            return User(user_data)
    except Exception as e:
        print(f"Error loading user {user_id}: {e}")
    return None
