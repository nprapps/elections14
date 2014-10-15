#!/usr/bin/env python

"""
Commands for rendering various parts of the app stack.
"""

from glob import glob
import os

from fabric.api import local, task

import app
import app_config

@task
def less():
    """
    Render LESS files to CSS.
    """
    for path in glob('less/*.less'):
        filename = os.path.split(path)[-1]
        name = os.path.splitext(filename)[0]
        out_path = 'www/css/%s.less.css' % name

        try:
            local('node_modules/less/bin/lessc %s %s' % (path, out_path))
        except:
            print 'It looks like "lessc" isn\'t installed. Try running: "npm install"'
            raise

@task
def jst():
    """
    Render Underscore templates to a JST package.
    """

    try:
        local('node_modules/universal-jst/bin/jst.js --template underscore jst www/js/templates.js')
    except:
        print 'It looks like "jst" isn\'t installed. Try running: "npm install"'

@task
def app_config_js():
    """
    Render app_config.js to file.
    """
    from static_app import _app_config_js

    response = _app_config_js()
    js = response[0]

    with open('www/js/app_config.js', 'w') as f:
        f.write(js)

@task
def copytext_js():
    """
    Render COPY to copy.js.
    """
    from static_app import _copy_js

    response = _copy_js()
    js = response[0]

    with open('www/js/copy.js', 'w') as f:
        f.write(js)

@task(default=True)
def render_all():
    """
    Render HTML templates and compile assets.
    """
    from flask import g

    less()
    jst()
    app_config_js()
    copytext_js()

    compiled_includes = {}

    for rule in app.app.url_map.iter_rules():
        rule_string = rule.rule
        name = rule.endpoint

        if name == 'static' or name.startswith('_'):
            print 'Skipping %s' % name
            continue

        if rule_string.endswith('/'):
            filename = 'www' + rule_string + 'index.html'
        elif rule_string.endswith('.html'):
            filename = 'www' + rule_string
        else:
            print 'Skipping %s' % name
            continue

        dirname = os.path.dirname(filename)

        if not (os.path.exists(dirname)):
            os.makedirs(dirname)

        print 'Rendering %s' % (filename)

        with app.app.test_request_context(path=rule_string):
            g.compile_includes = True
            g.compiled_includes = compiled_includes

            bits = name.split('.')

            # Determine which module the view resides in
            if len(bits) > 1:
                module, name = bits
            else:
                module = 'app'

            view = globals()[module].__dict__[name]
            content = view()

            compiled_includes = g.compiled_includes

        with open(filename, 'w') as f:
            if isinstance(content, tuple):
                content = content[0]
            f.write(content.encode('utf-8'))

@task
def render_slides():
    """
    Render slides to HTML files.

    NB: slides do not have embedded assets, so we don't pass
    the compile flag to the assets rig.
    """
    from flask import url_for
    import models

    slides = models.Slide.select()

    output_path = '.slides_html'

    for slide in slides:
        slug = slide.slug
        view_name = '_slide'

        if slug == 'state':
            continue

        # Silly fix because url_for require a context
        with app.app.test_request_context():
            path = url_for(view_name, slug=slug)

        with app.app.test_request_context(path=path):
            print 'Rendering %s' % path

            view = app.__dict__[view_name]
            content = view(slug)

        path = '%s%s' % (output_path, path)

        # Ensure path exists
        head = os.path.split(path)[0]

        try:
            os.makedirs(head)
        except OSError:
            pass

        with open(path, 'w') as f:
            f.write(content.data)

    render_states()

@task
def render_states(compiled_includes={}):
    """
    Render state slides to HTML files
    """
    from flask import url_for

    view_name = '_state_slide'
    output_path = '.slides_html'

    for postal, state in app_config.STATES.items():
        # Silly fix because url_for require a context
        with app.app.test_request_context():
            path = url_for(view_name, slug=postal)

        with app.app.test_request_context(path=path):
            print 'Rendering %s' % path

            view = app.__dict__[view_name]
            content = view(postal)

        path = '%s%s' % (output_path, path)

        # Ensure path exists
        head = os.path.split(path)[0]

        try:
            os.makedirs(head)
        except OSError:
            pass

        with open(path, 'w') as f:
            f.write(content.data)

@task
def render_big_boards(compiled_includes={}):
    from flask import g, url_for

    view_name = '_big_board'
    output_path = '.big_boards_html'

    for board in [
        'senate-big-board',
        'house-big-board-one',
        'house-big-board-two',
        'governor-big-board',
        'ballot-measures-big-board',
    ]:
        # Silly fix because url_for require a context
        with app.app.test_request_context():
            path = url_for(view_name, slug=board)

        with app.app.test_request_context(path=path):
            print 'Rendering %s' % path

            g.compile_includes = True
            g.compiled_includes = compiled_includes

            view = app.__dict__[view_name]
            content = view(board)

            compiled_includes = g.compiled_includes

        path = '%s%s' % (output_path, path)

        # Ensure path exists
        head = os.path.split(path)[0]

        try:
            os.makedirs(head)
        except OSError:
            pass

        with open('%sindex.html' % path, 'w') as f:
            f.write(content)
