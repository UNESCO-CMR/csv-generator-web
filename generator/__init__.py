from flask import Flask, redirect, url_for
import os
from flask_socketio import SocketIO
import eventlet
eventlet.monkey_patch()

socketio = SocketIO()


def create_app(environ=None, start_response=None, test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'generator.sqlite'),
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads'),
        GENERATED_DIR='generated',
        LOG_FILENAME='output.log',
        FILE_STATUSES={'Undone': -1, 'Ongoing': 0, 'Done': 1},
        PLATFORMS={'MY_SCHOOL_ONLINE': "MY SCHOOL ONLINE", 'MON_ECOLE_ENLIGNE': "MON ECOLE ENLIGNE"}
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
        os.makedirs(os.path.join(app.instance_path, '../instance/uploads'))
    except OSError:
        pass

    # @app.route('/')
    # def hello_world():
    #     return redirect(url_for('auth.login'))

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import region
    app.register_blueprint(region.bp)

    from . import files
    app.register_blueprint(files.bp)

    from . import user
    app.register_blueprint(user.bp)

    socketio.init_app(app)

    return app
