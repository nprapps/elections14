#!/usr/bin/env python

"""
Commands that render and copy the theme
"""

from fabric.api import execute, local, task, require
from fabric.state import env
import utils

import app
import app_config

@task
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
@task
def copytext_js():
    """
    Render COPY to copy.js.
    """
    from static import _copy_js

    response = _copy_js()
    js = response[0]

    with open('theme/www/js/copy.js', 'w') as f:
        f.write(js)

def app_config_js():
    """
    Render app_config.js to file.
    """
    from static import _app_config_js

    response = _app_config_js()
    js = response[0]

    with open('theme/www/js/app_config.js', 'w') as f:
        f.write(js)

@task(default=True)
def render():
    from flask import g

    require('settings', provided_by=['staging', 'production', 'development'])
    less()
    app_config_js()
    copytext_js('theme')

    compiled_includes = {}

    app_config.configure_targets(env.get('settings', None))

    with app.app.test_request_context():
        path = 'theme/www/index.html'

    with app.app.test_request_context(path=env.static_path):
        print 'Rendering %s' % path

        if env.settings == 'development':
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

@task
def deploy():
    """
    Deploy the latest app to S3 and, if configured, to our servers.
    """
    require('settings', provided_by=['production', 'staging'])

    execute('update')
    render()
    utils._gzip('theme/www/', '.gzip/theme/')
    utils._deploy_to_s3('.gzip/theme/')
