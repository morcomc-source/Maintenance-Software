from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models.user import User
from app import db
from sqlalchemy import func  # Added for case-insensitive query

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Make username case-insensitive
        user = User.query.filter(func.lower(User.username) == username.lower()).first()
        if user and user.check_password(password):
            login_user(user)
            if user.must_change_password:
                flash("Please change your password before continuing.", "warning")
                return redirect(url_for('auth.change_password'))
            return redirect(url_for('dashboard.index')) # Your dashboard route
        else:
            flash("Invalid username or password.", "danger")
    return render_template('auth/login.html') # Updated to include subfolder

@bp.route('/logout')
def logout():
    logout_user()
    session.pop('_flashes', None) # Clear any pending flashed messages
    return redirect(url_for('auth.login'))

# New: Password Change Route
@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
        elif len(new_password) < 8: # Add your validation rules, e.g., min length
            flash("Password must be at least 8 characters.", "danger")
        else:
            current_user.set_password(new_password, reset_flag=True)
            db.session.commit()
            flash("Password changed successfully.", "success")
            return redirect(url_for('dashboard.index')) # Or pm.index if preferred
    return render_template('auth/change_password.html') # Updated to include subfolder

# Add this if you have a registration route (optional, for completeness)
@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.index'))
    # ... your registration code, setting must_change_password=True for new users