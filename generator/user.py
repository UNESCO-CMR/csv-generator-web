from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from generator.auth import auth, admin
from generator.db import get_db

bp = Blueprint('user', __name__, url_prefix='/users')


def get_user_by_id(ID):
    return get_db().execute(
        "SELECT * FROM users WHERE id = ?", (ID,)
    ).fetchone()


@bp.route('/')
@auth
@admin
def index():
    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()
    return render_template("pages/users/index.html", users=users)


@bp.route('/change_status/<user_id>')
@auth
@admin
def change_status(user_id):
    user = get_user_by_id(user_id)
    error = None
    if user is None:
        error = "Unknown user identified."
    elif user['role'] == 'admin' and user['status']:
        error = "Please, first demote user before deactivating."

    if error is None:
        db = get_db()
        db.execute(
            "UPDATE users SET status = ? WHERE id = ?", (user['status'] == 0, user_id)
        )
        db.commit()
        flash("User's ({}) status updated successfully.".format(user['username']), 'success')
    else:
        flash(error, 'warning')

    return redirect(url_for('user.index'))


@bp.route('/promote_demote/<int:user_id>')
@auth
@admin
def promote_demote(user_id):
    user = get_user_by_id(user_id)
    error = None
    if user is None:
        error = "Unknown user identified."
    elif user['role'] == 'admin' and user['id'] == g.user['id']:
        error = "Fatal Error! Cannot demote yourself."
    elif not user['status']:
        error = "Cannot update role of an inactivate user. Please, first activate this user."

    if error is None:
        db = get_db()
        db.execute(
            "UPDATE users SET role = ? WHERE id = ?", (('editor' if user['role'] == 'admin' else 'admin'), user_id)
        )
        db.commit()
        flash("User's ({}) role updated successfully.".format(user['username']), 'success')
    else:
        flash(error, 'warning')

    return redirect(url_for('user.index'))
