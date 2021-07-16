from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from generator.auth import auth
from generator.db import get_db

bp = Blueprint('user', __name__)



def get_user_by_id(ID):
    return get_db().execute(
        "SELECT * FROM users WHERE id = ?", (ID, )
    ).fetchone()

