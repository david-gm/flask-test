import functools

from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

# A Blueprint is a way to organize a group of related views and other code.
# Rather than registering views and other code directly with an application, 
# they are registered with a blueprint. Then the blueprint is registered with
# the application when it is available in the factory function.
bp = Blueprint('auth', __name__, url_prefix='/auth')

# --> Import and register the blueprint in from the factory (__init__.py) using
# app.register_blueprint().

# @bp.router associates URL '/register' to register view function --> URL: /auth/register
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'User {} is already registered'.format(username)

        if error is None:
            db.execute(
                'INSERT INTO user (username, password) VALUES (?,?)',
                (username, generate_password_hash(password))
            )
            db.commit()
            flash('You were registered successfully. Please login now.')
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)
    return render_template('auth/login.html')

# bp.before_app_request() registers a function that runs before the view function,
# no matter what URL is requested. 
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        # user is stored in g.user, which lasts for the length of the request
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# create new decorator to check whether user is logged in
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            # NOTE: bluprint name ('auth') is prepended to the name of the view ('login')
            # seperated by a dash
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view