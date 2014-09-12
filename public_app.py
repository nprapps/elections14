#!/usr/bin/env python

import argparse
import datetime
import logging

from flask import Flask, render_template
from flask_peewee.auth import Auth
from flask_peewee.db import Database
from flask_peewee.admin import Admin
from models import Slide

import app_config
from render_utils import make_context

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['DATABASE'] = app_config.DATABASE
app.config['SECRET_KEY'] = 'askfhj3r3j'

file_handler = logging.FileHandler(app_config.APP_LOG_PATH)
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# Set up flask peewee db wrapper
db = Database(app)
auth = Auth(app, db)
admin = Admin(app, auth)
admin.register(Slide)
admin.setup()

# Example application views
@app.route('/%s/test/' % app_config.PROJECT_SLUG, methods=['GET'])
def _test_app():
    """
    Test route for verifying the application is running.
    """
    app.logger.info('Test URL requested.')

    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Example of rendering HTML with the rig
import static
from render_utils import urlencode_filter

app.register_blueprint(static.static, url_prefix='/%s' % app_config.PROJECT_SLUG)
app.jinja_env.filters['urlencode'] = urlencode_filter

@app.route ('/%s/' % app_config.PROJECT_SLUG, methods=['GET'])
def index():
    """
    Example view rendering a simple page.
    """
    return render_template('index.html', **make_context(asset_depth=1))

# Boilerplate
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port')
    args = parser.parse_args()
    server_port = 8080

    if args.port:
        server_port = int(args.port)

    app.run(host='0.0.0.0', port=server_port, debug=app_config.DEBUG)
