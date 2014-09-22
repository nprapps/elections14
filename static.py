#!/usr/bin/env python

import json
from mimetypes import guess_type
import subprocess

from flask import abort, Blueprint

import app_config
import copytext
from render_utils import flatten_app_config

static = Blueprint('static', __name__)

# Render JST templates on-demand
@static.route('/js/templates.js')
def _templates_js():
    r = subprocess.check_output(["node_modules/universal-jst/bin/jst.js", "--template", "underscore", "jst"])

    return r, 200, { 'Content-Type': 'application/javascript' }

# Render LESS files on-demand
def _less(filename, static_path=''):

    r = subprocess.check_output(["node_modules/less/bin/lessc", "%sless/%s" % (static_path, filename)])

    return r, 200, { 'Content-Type': 'text/css' }

# Render application configuration
def _app_config_js():
    config = flatten_app_config()
    js = 'window.APP_CONFIG = ' + json.dumps(config)

    return js, 200, { 'Content-Type': 'application/javascript' }

# Render copytext
def _copy_js():
    copy = 'window.COPY = ' + copytext.Copy(app_config.COPY_PATH).json()

    return copy, 200, { 'Content-Type': 'application/javascript' }

# Server arbitrary static files on-demand
def static_file(path, static_path=''):
    real_path = '%swww/%s' % (static_path, path)

    try:
        with open(real_path) as f:
            return f.read(), 200, { 'Content-Type': guess_type(real_path)[0] }
    except IOError:
        abort(404)