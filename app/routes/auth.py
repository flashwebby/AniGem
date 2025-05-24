from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db, add_user, find_user_by_username, find_user_by_email, update_user_last_login

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        
        if error is None:
            try:
                user_id = add_user(username, email, password)
                if user_id:
                    # Automatically log in the user after registration
                    session.clear()
                    session['user_id'] = user_id
                    update_user_last_login(user_id)
                    flash('Registration successful! You are now logged in.')
                    return redirect(url_for('auth.login')) # Or redirect to a profile page or homepage
                else:
                    # This else block might be redundant if add_user raises an exception for IntegrityError
                    error = f"User {username} or email {email} is already registered."
            except Exception as e: # Catching generic exception, ideally should be more specific
                error = f"An error occurred: {e}"


        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        identifier = request.form['identifier'] # Can be username or email
        password = request.form['password']
        db = get_db()
        error = None
        user = find_user_by_username(identifier)

        if user is None:
            user = find_user_by_email(identifier)

        if user is None:
            error = 'Incorrect username/email.'
        elif not user.check_password(password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            update_user_last_login(user.id)
            flash('Login successful!')
            # Redirect to a dashboard or home page, for now redirect to a placeholder
            # return redirect(url_for('index')) # Replace 'index' with your main page route
            return redirect(url_for('auth.test_login_success'))


        flash(error)

    return render_template('auth/login.html')

# Placeholder route for testing login success
@bp.route('/test_login_success')
def test_login_success():
    if 'user_id' not in session:
        return "Access Denied. Please login."
    return f"Login Successful! User ID: {session['user_id']}"


@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('auth.login')) # Or redirect to homepage

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        from app.db import find_user_by_id # Local import to avoid circular dependency if any
        g.user = find_user_by_id(user_id)

# Decorator for routes that require login
import functools

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view
