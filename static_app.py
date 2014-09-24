#!/usr/bin/env python

import json
from mimetypes import guess_type
import subprocess

from flask import abort, Blueprint

import app_config
import copytext
from render_utils import flatten_app_config

static_app = Blueprint('static_app', __name__)

# Render JST templates on-demand
@static_app.route('/js/templates.js')
def _templates_js():
    r = subprocess.check_output(["node_modules/universal-jst/bin/jst.js", "--template", "underscore", "jst"])

    return r, 200, { 'Content-Type': 'application/javascript' }

# Render LESS files on-demand
def less(filename, static_path=''):

    r = subprocess.check_output(["node_modules/less/bin/lessc", "%sless/%s" % (static_path, filename)])

    return r, 200, { 'Content-Type': 'text/css' }

# Render LESS files on-demand
@static_app.route('/less/<string:filename>')
def _less(filename):
    print filename
    return less(filename)

# Render application configuration
@static_app.route('/js/app_config.js')
def _app_config_js():
    config = flatten_app_config()
    js = 'window.APP_CONFIG = ' + json.dumps(config)

    return js, 200, { 'Content-Type': 'application/javascript' }

# render copytext
@static_app.route('/js/copy.js')
def _copy_js():
    copy = 'window.COPY = ' + copytext.Copy(app_config.COPY_PATH).json()

    return copy, 200, { 'Content-Type': 'application/javascript' }

def static(path, static_path=''):
    real_path = '%swww/%s' % (static_path, path)

    try:
        with open(real_path) as f:
            return f.read(), 200, { 'Content-Type': guess_type(real_path)[0] }
    except IOError:
        abort(404)

# serve arbitrary static files on-demand
@static_app.route('/<path:path>')
def _static(path):
    return static(path)