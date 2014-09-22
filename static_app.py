#!/usr/bin/env python

import json

from flask import Blueprint

from render_utils import flatten_app_config
import static

static_app = Blueprint('static_app', __name__)

# Render LESS files on-demand
@static_app.route('/less/<string:filename>')
def _post_less(filename):
    return static._less(filename)

# Render application configuration
@static_app.route('/js/app_config.js')
def _app_config_js():
    config = flatten_app_config()
    js = 'window.APP_CONFIG = ' + json.dumps(config)

    return js, 200, { 'Content-Type': 'application/javascript' }

# render copytext
@static_app.route('/js/copy.js')
def _copy_js():
    return static._copy_js()

# serve arbitrary static files on-demand
@static_app.route('/<path:path>')
def _post_static(path):
    return static.static_file(path)