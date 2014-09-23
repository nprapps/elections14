#!/usr/bin/env python

"""
Commands that render and copy the theme
"""

from glob import glob
import os

from fabric.api import local, task, require
from fabric.state import env
import utils

import app
import app_config
import static_theme

@task(default=True)
def render():
    """
    Render the Tumblr theme.
    """
    from flask import g
    
    less()
    app_config_js()

    compiled_includes = {}

    app_config.configure_targets(env.get('settings', None))

    with app.app.test_request_context():
        path = 'theme/www/index.html'

    with app.app.test_request_context(path='/theme'):
        print 'Rendering %s' % path

        if env.settings not in ['staging', 'production']:
            g.compile_includes = False
        else:
            g.compile_includes = True

        g.compiled_includes = compiled_includes

        view = static_theme.__dict__['_theme']
        content = view()

    with open(path, 'w') as f:
        f.write(content.encode('utf-8'))

    local('pbcopy < theme/www/index.html')
    print 'The Tumblr theme HTML has been copied to your clipboard.'
    local('open https://www.tumblr.com/customize/%s' % app_config.TUMBLR_NAME)

def less():
    """
    Render LESS files to CSS.
    """
    for path in glob('theme/less/*.less'):
        filename = os.path.split(path)[-1]
        name = os.path.splitext(filename)[0]
        out_path = 'theme/www/css/%s.less.css' % name

        try:
            local('node_modules/less/bin/lessc %s %s' % (path, out_path))
        except:
            print 'It looks like "lessc" isn\'t installed. Try running: "npm install"'
            raise

def app_config_js():
    """
    Render Tumblr theme app_config.js to file.
    """
    from static_theme import _app_config_js

    response = _app_config_js()
    js = response[0]

    with open('theme/www/js/app_config.js', 'w') as f:
        f.write(js)

@task
def deploy():
    """
    Deploy the latest Tumblr theme assets to S3.
    """
    require('settings', provided_by=['production', 'staging'])

    #execute('update')
    render()
    utils._gzip('theme/www/', '.gzip_theme/theme')
    utils._deploy_to_s3('.gzip_theme')
