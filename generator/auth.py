import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from generator.db import get_db

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
        elif db.execute(
                'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = f"User {username} is already registered."

        if error is None:
            db.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, generate_password_hash(password))
            )
            db.commit()
            flash('Registration successful. Please, login to continue...', 'success')
            return redirect(url_for('auth.login'))

        flash(error, 'warning')

    return render_template("pages/auth/register.html")


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        elif not user['status']:
            error = "THANKS FOR LOGGING IN! Your account is still awaiting activation. Please, contact the " \
                    "Administrator to grant you access. Sorry about this. "

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('region.index'))  # @todo Change index appropriately

        flash(error, 'warning')

    return render_template("pages/auth/login.html")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


def auth(view):
    @functools.wraps(view)
    def wrapped_views(**kwargs):
        if g.user is None:
            flash("Please login to continue.", "warning")
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_views


def guest(view):
    @functools.wraps(view)
    def wrapped_views(**kwargs):
        if g.user is not None:
            flash("You are already logged  in. Please logout to continue.", "primary")
            return redirect(url_for('region.index'))  # @todo Change index appropriately

        return view(**kwargs)

    return wrapped_views


def admin(view):
    @functools.wraps(view)
    def wrapped_views(**kwargs):
        if g.user['role'] != 'admin':
            flash("You are not authorized to access this resource.", "danger")
            return redirect(url_for('region.index'))

        return view(**kwargs)

    return wrapped_views


def redirect_back(default='region.index'):
    return request.args.get('next') or request.referrer or url_for(default)
