#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import argparse
from flask import Flask, render_template
from peewee import fn

import app_config
from render_utils import make_context, smarty_filter, urlencode_filter
import static

app = Flask(__name__)

app.jinja_env.filters['smarty'] = smarty_filter
app.jinja_env.filters['urlencode'] = urlencode_filter

# Example application views
@app.route('/')
def index():
    """
    Example view demonstrating rendering a simple HTML page.
    """
    from models import Race

    context = make_context()

    with open('data/featured.json') as f:
        context['featured'] = json.load(f)

    context['races'] = Race.select()

    return render_template('index.html', **context), 200, 

@app.route('/chromecast/')
def chromecast():
    """
    Custom Chromecast receiver.
    """
    context = make_context()

    return render_template('chromecast.html', **context)

@app.route('/game/')
def game():
    """
    Custom Chromecast receiver.
    """
    context = make_context()

    secrets = app_config.get_secrets()
    context['DYNAMODB_ACCESS_KEY_ID'] = secrets['DYNAMODB_ACCESS_KEY_ID']
    context['DYNAMODB_SECRET_ACCESS_KEY'] = secrets['DYNAMODB_SECRET_ACCESS_KEY']

    return render_template('game.html', **context)

@app.route('/results/house/')
def results_house():
    """
    House big board
    """
    context = make_context()

    return render_template('slides/house.html', **context)

@app.route('/results/senate/')
def results_senate():
    """
    Senate big board
    """
    context = make_context()

    return render_template('slides/senate.html', **context)

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
def _slide(slug):
    """
    Serve up slide html fragment
    """
    from models import Slide

    slide = Slide.get(Slide.slug == slug)
    return render_template('_stack_fragment.html', body=slide.body)

@app.route('/live-data/next-slide.json')
def _stack_json():
    """
    Serve up pointer to next slide in stack
    """
    from models import SlideSequence

    if not hasattr(app, 'stack_number'):
        min_sequence = SlideSequence.select(fn.Min(SlideSequence.sequence)).scalar()
        app.stack_number = min_sequence

    max = SlideSequence.select(fn.Max(SlideSequence.sequence)).scalar()
    if app.stack_number > max:
        min = SlideSequence.select(fn.Min(SlideSequence.sequence)).scalar()
        app.stack_number = min

    next_slide = SlideSequence.get(SlideSequence.sequence == app.stack_number)
    app.stack_number += 1

    js = json.dumps({
        'next': 'slides/%s.html' % next_slide.slide.slug,
    })
    return js, 200, { 'Content-Type': 'application/javascript' }

@app.route('/stack/')
def stack():
    """
    Serve shell page for stack
    """
    context = make_context()

    return render_template('stack.html', **context)

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
