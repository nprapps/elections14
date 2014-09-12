#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import yaml

import argparse
from flask import Flask, render_template

import app_config
from render_utils import make_context, smarty_filter, urlencode_filter
import static

from models import Slide, SlideSequence

app = Flask(__name__)

app.jinja_env.filters['smarty'] = smarty_filter
app.jinja_env.filters['urlencode'] = urlencode_filter

# Example application views
@app.route('/')
def index():
    """
    Example view demonstrating rendering a simple HTML page.
    """
    context = make_context()

    with open('data/featured.json') as f:
        context['featured'] = json.load(f)

    with open('www/live-data/init.json') as f:
        context['races'] = json.load(f)

    return render_template('index.html', **context)

@app.route('/chromecast/')
def chromecast():
    """
    Custom Chromecast receiver.
    """
    context = make_context()

    return render_template('chromecast.html', **context)

@app.route('/comments/')
def comments():
    """
    Full-page comments view.
    """
    return render_template('comments.html', **make_context())

@app.route('/widget.html')
def widget():
    """
    Embeddable widget example page.
    """
    return render_template('widget.html', **make_context())

@app.route('/test_widget.html')
def test_widget():
    """
    Example page displaying widget at different embed sizes.
    """
    return render_template('test_widget.html', **make_context())

@app.route('/slides/<slug>.html')
def slide(slug):
    """
    Serve up slide html fragment
    """
    slide = Slide.get(Slide.slug == slug)
    return render_template('_stack_fragment.html', body=slide.body)

@app.route('/stack.json')
def stack_json():
    """
    Serve up pointer to next slide in stack
    """

    if app.stack_number > 4:
        app.stack_number = 1

    #import ipdb; ipdb.set_trace();

    next_slide = SlideSequence.get(SlideSequence.sequence == app.stack_number)
    app.stack_number += 1

    js = json.dumps({
        'next': '/slides/%s.html' % next_slide.slide.__unicode__(),
    })
    return js, 200, { 'Content-Type': 'application/javascript' }

@app.route('/stack.html')
def stack():
    """
    Serve shell page for stack
    """
    return render_template('stack.html', **make_context())


app.stack_number = 1
app.register_blueprint(static.static)

# Boilerplate
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port')
    args = parser.parse_args()
    server_port = 8000

    if args.port:
        server_port = int(args.port)

    app.run(host='0.0.0.0', port=server_port, debug=app_config.DEBUG)
