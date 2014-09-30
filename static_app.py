#!/usr/bin/env python

import json
from mimetypes import guess_type
import subprocess

from flask import abort, Blueprint

import app_config
import copytext
from render_utils import BetterJSONEncoder, flatten_app_config

static_app = Blueprint('static_app', __name__)

@static_app.route('/js/templates.js')
def _templates_js():
    """
    Render JST templates.
    """
    r = subprocess.check_output(["node_modules/universal-jst/bin/jst.js", "--template", "underscore", "jst"])

    return r, 200, { 'Content-Type': 'application/javascript' }

def less(filename, static_path=''):
    """
    Render LESS files.
    """
    r = subprocess.check_output(["node_modules/less/bin/lessc", ('%s/less/%s' % (static_path, filename)).lstrip('/')])

    return r, 200, { 'Content-Type': 'text/css' }

@static_app.route('/less/<string:filename>')
def _less(filename):
    return less(filename)

@static_app.route('/js/app_config.js')
def _app_config_js():
    """
    Render app configuration to javascript.
    """
    config = flatten_app_config()
    js = 'window.APP_CONFIG = ' + json.dumps(config, cls=BetterJSONEncoder)

    return js, 200, { 'Content-Type': 'application/javascript' }

@static_app.route('/js/copy.js')
def _copy_js():
    """
    Render copytext to javascript.
    """
    copy = 'window.COPY = ' + copytext.Copy(app_config.COPY_PATH).json()

    return copy, 200, { 'Content-Type': 'application/javascript' }

def static(path, static_path=''):
    """
    Serve arbitrary files.
    """
    real_path = ('%s/www/%s' % (static_path, path)).lstrip('/')

    try:
        with open(real_path) as f:
            return f.read(), 200, { 'Content-Type': guess_type(real_path)[0] }
    except IOError:
        abort(404)

@static_app.route('/<path:path>')
def _static(path):
    return static(path)
