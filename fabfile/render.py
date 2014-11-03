#!/usr/bin/env python

"""
Commands for rendering various parts of the app stack.
"""
import app
import app_config
import multiprocessing
import os

from fabric.api import local, task
from glob import glob
from joblib import Parallel, delayed

NUM_CORES = multiprocessing.cpu_count() * 4

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
def render_liveblog():
    """
    Render liveblog slides to HTML files.
    """
    import models

    output_path = '.liveblog_slides_html'

    try:
        os.makedirs(output_path)
    except OSError:
        pass

    slides = models.Slide.select()
    slugs = [slide.slug for slide in slides if slide.slug.startswith('tumblr')]
    slides.database.close()

    Parallel(n_jobs=NUM_CORES)(delayed(_render_liveblog_slide)(slug, output_path) for slug in slugs)
    print "Rendered liveblog"

def _render_liveblog_slide(slug, output_path):
    """
    Render a liveblog slide
    """
    from flask import url_for

    for view_name in ['_slide', '_slide_preview']:
        with app.app.test_request_context():
            path = url_for(view_name, slug=slug)

        with app.app.test_request_context(path=path):
            #print 'Rendering %s' % path

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

@task
def render_results():
    """
    Render results slides to HTML files.

    NB: slides do not have embedded assets, so we don't pass
    the compile flag to the assets rig.
    """
    import models

    output_path = '.results_slides_html'
    try:
        os.makedirs(output_path)
    except OSError:
        pass

    slides = models.Slide.select()
    slugs = [slide.slug for slide in slides if slide.slug not in ['state-senate-results', 'state-house-results'] and not slide.slug.startswith('tumblr')]
    slides.database.close()

    Parallel(n_jobs=NUM_CORES)(delayed(_render_results_slide)(slug, output_path) for slug in slugs)
    print "Rendered results"

def _render_results_slide(slug, output_path):
    from flask import url_for

    for view_name in ['_slide', '_slide_preview']:
        with app.app.test_request_context():
            path = url_for(view_name, slug=slug)

        with app.app.test_request_context(path=path):
            #print 'Rendering %s' % path

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

@task
def render_states(compiled_includes={}):
    """
    Render state slides to HTML files
    """

    output_path = '.state_slides_html'
    Parallel(n_jobs=NUM_CORES)(delayed(_render_state)(postal, state, output_path) for postal, state in app_config.STATES.items())
    print "Rendered states"

def _render_state(postal, state, output_path):
    """
    Render a state.
    """
    from flask import url_for
    to_render = [
        ('_state_senate_slide', { 'slug': postal }),
        ('_state_senate_slide_preview', { 'slug': postal }),
        ('_state_house_slide', { 'slug': postal, 'page': 1 }),
        ('_state_house_slide_preview', { 'slug': postal, 'page': 1 })
    ]

    if postal in app_config.PAGINATED_STATES:
        to_render.extend([
            ('_state_house_slide', { 'slug': postal, 'page': 2 }),
            ('_state_house_slide_preview', { 'slug': postal, 'page': 2 })
        ])

    for view_name, view_kwargs in to_render:
        # Silly fix because url_for require a context
        with app.app.test_request_context():
            path = url_for(view_name, **view_kwargs)

        with app.app.test_request_context(path=path):
            view = app.__dict__[view_name]
            content = view(**view_kwargs)

        if content.status_code == 200:
            #print 'Rendering %s (%s)' % (path, content.status_code)

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
def render_big_boards():
    """
    Render big boards
    """
    output_path = '.big_boards_html'

    boards = [
        'senate-big-board',
        'house-big-board-one',
        'house-big-board-two',
        'governor-big-board',
        'ballot-measures-big-board',
    ]
    Parallel(n_jobs=NUM_CORES)(delayed(_render_bigboard_slide)('_big_board', board, output_path) for board in boards)
    print "Rendered big boards"

def _render_bigboard_slide(view_name, slug, output_path):
    """
    Render a slide
    """
    from flask import url_for

    # Silly fix because url_for requires a context
    with app.app.test_request_context():
        path = url_for(view_name, slug=slug)

    with app.app.test_request_context(path=path):
        #print 'Rendering %s' % path
        view = app.__dict__[view_name]
        content = view(slug)

    path = '%s%s' % (output_path, path)

    # Ensure path exists
    head = os.path.split(path)[0]

    try:
        os.makedirs(head)
    except OSError:
        pass

    with open('%sindex.html' % path, 'w') as f:
        f.write(content)

@task
def render_bop():
    from flask import g, url_for

    view_name = '_bop'
    output_path = '.bop_html'

    with app.app.test_request_context():
        path = url_for(view_name)

    with app.app.test_request_context(path=path):
        view = app.__dict__[view_name]
        content = view()

    path = '%s%s' % (output_path, path)

    # Ensure path exists
    head = os.path.split(path)[0]

    try:
        os.makedirs(head)
    except OSError:
        pass

    with open('%s' % path, 'w') as f:
        f.write(content.data)
