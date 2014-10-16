#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import argparse
from flask import Flask, render_template

import app_config
import app_utils
from render_utils import make_context, smarty_filter, urlencode_filter
import slides
import static_app
import static_theme

app = Flask(__name__)

app.jinja_env.filters['smarty'] = smarty_filter
app.jinja_env.filters['urlencode'] = urlencode_filter

@app.template_filter()
def format_board_time(dt):
    """
    Format a time for the big board
    """
    if not dt:
        return ''

    return '{d:%l}:{d.minute:02}'.format(d=dt)

@app.template_filter()
def format_percent(num):
    """
    Format a percentage
    """
    return int(round(num))

@app.template_filter()
def signed(num):
    """
    Add sign to number (e.g. +1, -1)
    """
    return '{0:+d}'.format(num)

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

    """
    Balance of Power data
    """
    races = Race.select().where(Race.office_name == 'U.S. Senate').order_by(Race.state_postal)

    context['bop'] = app_utils.calculate_bop(races, app_utils.SENATE_MAJORITY, app_utils.SENATE_INITIAL_BOP)
    context['not_called'] = app_utils.calculate_seats_left(races)

    return render_template('index.html', **context), 200,

@app.route('/comments/')
def comments():
    """
    Full-page comments view.
    """
    return render_template('comments.html', **make_context())

@app.route('/board/<slug>/')
def _big_board(slug):
    """
    Preview a slide outside of the stack.
    """
    context = make_context()

    context['body'] = _slide(slug).data

    return render_template('_big_board_wrapper.html', **context)

@app.route('/live-data/stack.json')
@app_utils.cors
def _stack_json():
    """
    Serve up the current slide stack.
    """
    from models import SlideSequence

    data = SlideSequence.stack()
    js = json.dumps(data)

    return js, 200, { 'Content-Type': 'application/javascript' }

@app.route('/preview/state-<slug>/')
def _state_slide_preview(slug):
    """
    Preview a state slide outside of the stack.
    """
    context = make_context()

    context['body'] = _state_slide(slug).data

    return render_template('_slide_preview.html', **context)

@app.route('/preview/<slug>/')
def _slide_preview(slug):
    """
    Preview a slide outside of the stack.
    """
    context = make_context()

    context['body'] = _slide(slug).data

    return render_template('_slide_preview.html', **context)

@app.route('/slides/state-<slug>.html')
@app_utils.cors
def _state_slide(slug):
    """
    Serve a state slide.
    """
    from models import Race

    slug = slug.upper()

    context = make_context()
    context['state_postal'] = slug
    context['state_name'] = app_config.STATES.get(slug)

    context['senate'] = Race.select().where(
        (Race.office_name == 'U.S. Senate') &
        (Race.state_postal == slug)
    ).order_by(Race.seat_number)

    context['governor'] = Race.select().where(
        (Race.office_name == 'Governor') &
        (Race.state_postal == slug)
    )

    context['house'] = Race.select().where(
        (Race.office_name == 'U.S. House') &
        (Race.state_postal == slug) &
        (Race.featured_race == True)
    ).order_by(Race.seat_number)

    context['body'] = render_template('slides/state.html', **context)

    return render_template('_slide.html', **context)

@app.route('/slides/<slug>.html')
@app_utils.cors
def _slide(slug):
    """
    Serve up slide html fragment
    """
    from models import Slide

    slide = Slide.get(Slide.slug == slug)
    view_name = slide.view_name

    if view_name == '_slide':
        body = slide.body
    else:
        body = slides.__dict__[view_name]()

    return render_template('_slide.html', body=body)

app.register_blueprint(static_app.static_app)
app.register_blueprint(static_theme.theme)

# Boilerplate
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port')
    args = parser.parse_args()
    server_port = 8000

    if args.port:
        server_port = int(args.port)

    app.run(host='0.0.0.0', port=server_port, debug=app_config.DEBUG)
