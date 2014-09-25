#!/usr/bin/env python

from flask import Blueprint, render_template
from render_utils import make_context
import static_app

import app_config

theme = Blueprint(
    'theme',
    __name__,
    url_prefix='/theme',
    template_folder='theme/templates'
)

@theme.route('/less/<string:filename>')
def _theme_less(filename):
    """
    Render LESS files.
    """
    return static_app.less(filename, 'theme')

@theme.route('/js/app_config.js')
def _app_config_js():
    """
    Render app configuration to javascript.
    """
    return static_app._app_config_js()

@theme.route('/js/copy.js')
def _copy_js():
    """
    Render copytext to javascript.
    """
    return static_app._copy_js()

@theme.route('/<path:path>')
def _theme_static(path):
    """
    Serve arbitrary files.
    """
    return static_app.static(path, 'theme')

@theme.route('/theme')
def _theme():
    context = make_context(static_path='theme', absolute=True)

    context['tumblr_name'] = app_config.TUMBLR_NAME

    return render_template('theme.html', **context)
