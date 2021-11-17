import collections

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


@bp.route('/statistics')
@auth
@admin
def statistics():
    db = get_db()
    users = db.execute(
        "SELECT u.id, u.username"
        # ", SUM(c.females) AS females, SUM(c.males) AS males "
        " FROM users u "
        # "LEFT JOIN cleaned_files AS c ON c.user_id = u.id"
        " WHERE (SELECT COUNT(*) > 0 FROM cleaned_files AS cf WHERE u.id = cf.user_id) "
    ).fetchall()
    # SQL = "SELECT u.id AS user_id, u.username AS username FROM users u " \
    #       "LEFT JOIN cleaned_files c ON u.id = c.user_id WHERE u.status = 1 UNION ALL " \
    # "SELECT u.id AS user_id, u.username AS username FROM users u " \
    # "RIGHT JOIN cleaned_files c ON u.id = c.user_id WHERE u.status = 1"
    stats = []
    users = [dict(u) for u in users]
    for index, user in enumerate(users):
        cleaned = db.execute("SELECT * FROM cleaned_files AS cf WHERE cf.user_id = ?", (user['id'],)).fetchall()
        females = sum(map(lambda x: x['females'], cleaned))
        males = sum(map(lambda x: x['males'], cleaned))
        users[index]['females'] = females
        users[index]['males'] = males
        users[index]['total'] = males + females
    users = sorted(users, key=lambda x: x['total'], reverse=True)
    return render_template("pages/users/stats.html", users=users)


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
