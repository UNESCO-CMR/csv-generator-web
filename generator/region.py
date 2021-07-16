from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from generator.auth import auth
from generator.db import get_db

bp = Blueprint('region', __name__)


@bp.route('/')
@auth
def index():
    db = get_db()
    regions = db.execute(
        "SELECT regions.id, regions.name, regions.abbr, regions.created_on, COUNT(files.id) AS files FROM regions LEFT "
        "JOIN files ON files.region_id = regions.id GROUP BY regions.id"
    ).fetchall()

    return render_template("pages/index.html", regions=regions)


@bp.route('/create-region', methods=('GET', 'POST'))
@auth
def create_region():
    if request.method == 'POST':
        name = request.form['name']
        abbr = request.form['abbr']
        error = None

        if name is None:
            error = "Name is required."
        elif abbr is None:
            error = "Abbreviation is required."

        if error is None:
            db = get_db()
            db.execute(
                "INSERT INTO regions (name, abbr, user_id) VALUES (?, ?, ?)", (name, abbr, g.user['id'])
            )
            db.commit()

            flash("Region created successfully.", "success")
            return redirect(url_for('region.index'))

        flash(error, "warning")

    return render_template('pages/regions/create.html')


def get_region_by_id(ID):
    return get_db().execute(
        "SELECT * FROM regions WHERE id = ?", (ID, )
    ).fetchone()

