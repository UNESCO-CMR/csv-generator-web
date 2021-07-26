import ntpath
import os
import shutil
from datetime import datetime as dt

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, send_from_directory
)
from glob2 import glob
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
import uuid
from urllib.parse import unquote

from generator.auth import auth, redirect_back
from generator.db import get_db
from generator.region import get_region_by_id
from generator.user import get_user_by_id
from generator.util import main as gen_master

bp = Blueprint('file', __name__)
ALLOWED_EXTENSIONS = {'xlsx', 'xlsm', 'xlsb', 'xltx', 'xltm', 'xlt', 'xls', 'xml', 'xml', 'xlam', 'xla', 'xlw', 'xlr'}


@bp.route('/<string:name>')
@auth
def index(name):
    db = get_db()
    SQL = "SELECT * FROM regions WHERE name LIKE {}%{}%{}".format("'", unquote(name).strip(), "'")
    region = db.execute(SQL).fetchone()
    
    if region is not None:
        files = db.execute(
            "SELECT f.title, f.filename, f.created_on, f.id, f.region_id, f.status, f.user_id, u.username as user"
            " FROM files AS f "
            "INNER JOIN regions AS r ON f.region_id = r.id "
            "INNER JOIN users AS u ON f.user_id = u.id "
            # "LEFT JOIN generated_files ON files.id = generated_files.file_id "
            # "INNER JOIN users ON files.user_id = users.id"
            "WHERE r.id = ? ", (region['id'],)
        ).fetchall()
        return render_template("pages/files/list.html", region=region, files=files)

    flash("The specified data does not exists", "warning")
    return redirect(url_for("region.index"))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/create-file/<string:name>', methods=('GET', 'POST'))
@auth
def create_file(name):
    db = get_db()
    region = db.execute(
        "SELECT * FROM regions WHERE name = ?", (name,)
    ).fetchone()
    print(region)
    if request.method == 'POST':
        title = request.form['title']
        error = None

        if 'file' not in request.files:
            error = "No file was selected. Please, choose a file"
        elif not allowed_file(request.files['file'].filename):
            error = "The selected file is invalid. Please, choose a file with either of the extensions: " + ", ".join(
                ALLOWED_EXTENSIONS)
        elif title is None:
            error = "Please, enter a title"

        if error is None:
            file = request.files['file']
            if file:
                filename = secure_filename(str(uuid.uuid4().hex))
                file_ext = os.path.splitext(file.filename)[1]
                full_name = filename + file_ext
                save_dir = os.path.join(filename)
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], save_dir)
                try:
                    os.makedirs(save_path)
                except OSError:
                    flash(f"Error creating directory: {save_path}", "danger")
                    return redirect(url_for('file.create_file', name=name))

                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], save_dir, full_name))

                db.execute(
                    "INSERT INTO files (title, path, filename, region_id, user_id) VALUES (?, ?, ?, ?, ?)",
                    (title, save_dir, full_name, region['id'], g.user['id'])
                )
                db.commit()

                flash("File successfully added to server.", "success")

                if 'save_add_another' in request.form and request.form['save_add_another']:
                    return redirect(url_for('file.create_file', name=name))

                return redirect(url_for('file.index', name=name))

        flash(error, "warning")

    return render_template('pages/files/create.html', region=region)


def update_file_status(ID, status=None):
    db = get_db()
    file = get_file_by_id(ID)

    current_status = file['status']
    if status is None:
        status = 0 if current_status == 1 else current_status + 1

    db.execute(
        "UPDATE files SET status = ? WHERE id = ?", (status, ID)
    )
    db.execute(
        "INSERT INTO file_statuses (user_id, file_id, 'from', 'to') VALUES (?, ?, ?, ?)",
        (g.user['id'], ID, current_status, status)
    )
    db.commit()
    flash("Status updated successfully.", 'success')


@bp.route('/status/<int:ID>')
def change_status(ID):
    update_file_status(ID)

    return redirect(redirect_back())


@bp.route('/remove/<int:ID>')
def remove_cleaned_file(ID):
    cleaned_file = get_cleaned_file_by_id(ID)
    update_file_status(cleaned_file['file_id'], current_app.config['FILE_STATUSES']['Ongoing'])
    clean_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cleaned_file['path'], cleaned_file['filename'])
    if os.path.isfile(clean_path):
        os.remove(clean_path)
    gen_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cleaned_file['path'], current_app.config['GENERATED_DIR'])
    if os.path.isdir(gen_path):
        shutil.rmtree(gen_path)
    db = get_db()
    db.execute(
        "DELETE FROM cleaned_files WHERE id = ?", (ID,)
    )
    db.commit()
    flash("File delete successfully.", 'info')
    return redirect(redirect_back())


@bp.route('/download/<ID>')
def download_file(ID):
    file = get_file_by_id(ID)
    if not file:
        flash("The specified file does not exists.", "warning")
        return redirect(url_for("region.index"))

    return send_from_directory(os.path.join(current_app.config['UPLOAD_FOLDER'], file['path']), file['filename'],
                               as_attachment=True,
                               attachment_filename="{}_{}{}".format(secure_filename(file['title']), str(dt.now()),
                                                                    os.path.splitext(file['filename'])[1]))


@bp.route('/download/<int:ID>/<filename>')
def download_generated_file(ID, filename):
    cleaned_file = get_cleaned_file_by_id(ID)
    if not cleaned_file:
        flash("The specified file does not exists.", "warning")
        return redirect(url_for("region.index"))

    return send_from_directory(
        os.path.join(current_app.config['UPLOAD_FOLDER'], cleaned_file['path'], current_app.config['GENERATED_DIR']),
        filename, as_attachment=True, attachment_filename="{}_{}{}".format(secure_filename(os.path.splitext(filename)[0]), str(dt.now()),
                                                                           os.path.splitext(filename)[1]))


@bp.route('/download-clean/<ID>')
def download_cleaned_file(ID):
    cleaned_file = get_cleaned_file_by_id(ID)
    if not cleaned_file:
        flash("The specified file does not exists.", "warning")
        return redirect(url_for("region.index"))

    return send_from_directory(os.path.join(current_app.config['UPLOAD_FOLDER'], cleaned_file['path']),
                               cleaned_file['filename'],
                               as_attachment=True,
                               attachment_filename="{}_{}{}".format(secure_filename(cleaned_file['title']),
                                                                    str(dt.now()),
                                                                    os.path.splitext(cleaned_file['filename'])[1]))


@bp.route('/explore/<string:title>')
def explore_file(title):
    file = get_file_by_title(title)
    region = get_region_by_id(file['region_id'])
    user = get_user_by_id(file['user_id'])
    statuses = get_db().execute(
        "SELECT s.*, u.username FROM file_statuses AS s"
        " LEFT JOIN users as u ON  u.id = s.user_id "
        " WHERE s.file_id = ?", (file['id'],)
    ).fetchall()
    cleaned_file = get_db().execute(
        "SELECT c.*, u.username FROM cleaned_files as c "
        "LEFT JOIN users as u ON  u.id = c.user_id "
        "WHERE file_id = ?", (file['id'],)
    ).fetchone()

    # Get generated file list from directory
    output_log = None
    generated_files = None
    if cleaned_file:
        generated_files = [ntpath.basename(path) for path in glob(
            "{}/{}/*.csv".format(os.path.join(current_app.config['UPLOAD_FOLDER'], cleaned_file['path']),
                                 current_app.config['GENERATED_DIR']))]
        generated_files = generated_files if len(generated_files) else None
        # Get output generation logs
        log_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cleaned_file['path'],
                                current_app.config['LOG_FILENAME'])
        if os.path.isfile(log_path):
            with open(log_path, 'r') as f:
                output_log = "".join(f.readlines())
    return render_template("pages/gens/index.html", file=file, region=region, user=user, statuses=statuses,
                           cleaned=cleaned_file, generated=generated_files, log_data=output_log)


@bp.route('/upload_cleaned/<int:file_id>', methods=('POST',))
def add_cleaned_file(file_id):
    db = get_db()
    file = get_file_by_id(file_id)
    error = None

    if 'cleaned_file' not in request.files:
        error = "No file was selected. Please, choose a file"
    elif not allowed_file(request.files['cleaned_file'].filename):
        error = "The selected file is invalid. Please, choose a file with either of the extensions: " + ", ".join(
            ALLOWED_EXTENSIONS)

    if error is None:
        title = "{}_{}".format(
            os.path.splitext(request.files['cleaned_file'].filename)[0], "CLEANED")
        cleaned_file = request.files['cleaned_file']
        if cleaned_file:
            filename = secure_filename(str(uuid.uuid4().hex)) + "_CLEANED"
            file_ext = os.path.splitext(cleaned_file.filename)[1]
            full_name = filename + file_ext
            save_dir = os.path.join(file['path'])
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], save_dir, full_name)

            cleaned_file.save(save_path)

            db.execute(
                "INSERT INTO cleaned_files (title, path, filename, file_id, user_id) VALUES (?, ?, ?, ?, ?)",
                (title, save_dir, full_name, file_id, g.user['id'])
            )
            db.commit()

            flash("Cleaned file successfully uploaded.", "success")

            return redirect(url_for('file.change_status', ID=file['id']))

    flash(error, "warning")
    return redirect(url_for('file.explore_file', title=file['title']))


@bp.route('/generate-csv/<int:cleaned_id>')
def generate_csv(cleaned_id):
    cleaned = get_cleaned_file_by_id(cleaned_id)
    save_dir = current_app.config['GENERATED_DIR']
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cleaned['path'], save_dir)

    try:
        os.makedirs(save_path)
    except OSError:
        pass

    config = {
        'FILENAME': os.path.join(current_app.config['UPLOAD_FOLDER'], cleaned['path'], cleaned['filename']),
        'SAVE_PATH': save_path,
        'UPDATE_USERNAME': True,
        'UPDATE_NAMES': True,
        'UPDATE_PASSWORD': True,
        'EXPORT_CSV': True,
        'CSV_DELIMITER': ";",
        'PASSWORD_LENGTH': 1,
        'LOG_FILE': os.path.join(current_app.config['UPLOAD_FOLDER'], cleaned['path'],
                                 current_app.config['LOG_FILENAME'])
    }
    print(config['FILENAME'])
    _ = gen_master(config)
    with open(config['LOG_FILE'], 'r') as f:
        log = f.readlines()

    flash("***".join(log), "info")
    return redirect(redirect_back())


def get_file_by_id(ID):
    return get_db().execute(
        "SELECT * FROM files WHERE id = ?", (ID,)
    ).fetchone()


def get_cleaned_file_by_id(ID):
    return get_db().execute(
        "SELECT * FROM cleaned_files WHERE id = ?", (ID,)
    ).fetchone()


def get_file_by_title(title):
    return get_db().execute(
        "SELECT * FROM files WHERE title = ?", (title,)
    ).fetchone()
