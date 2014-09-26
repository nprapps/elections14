#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps
import json

import argparse
from flask import Flask, make_response, render_template

import app_config
from render_utils import make_context, smarty_filter, urlencode_filter
import static_app
import static_theme

app = Flask(__name__)

app.jinja_env.filters['smarty'] = smarty_filter
app.jinja_env.filters['urlencode'] = urlencode_filter

STACK_NUMBER_FILENAME = '.stack_number'

SENATE_MAJORITY = 51
SENATE_INITIAL_BOP = {
    'dem': 32,
    'gop': 30,
    'other': 2,
}

HOUSE_MAJORITY = 218
HOUSE_INITIAL_BOP = {
    'dem': 0,
    'gop': 0,
    'other': 0,
}

def _group_races_by_closing_time(races):
    """
    Process race results for use in templates.
    """
    results = {}

    for race in races:
        if not results.get(race.poll_closing_time):
            results[race.poll_closing_time] = []

        results[race.poll_closing_time].append(race)

    return sorted(results.items())

def _calculate_bop(races, majority, initial):
    """
    Calculate a balance of power
    """
    bop = {key: {
        'has': value,
        'needs': majority - value,
        'picked_up': 0,
    } for key, value in initial.items()}

    winning_races = [race for race in races if race.is_called()]
    for race in winning_races:
        winner = race.get_winning_party()

        bop[winner]['has'] += 1
        if bop[winner]['needs'] > 0:
            bop[winner]['needs'] -= 1

        if race.party_changed():
            bop[winner]['picked_up'] += 1
            bop[race.previous_party]['picked_up'] -= 1

    return bop

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

def cors(f):
    """
    Decorator that enables local CORS support for easier local dev.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    return decorated_function

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

@app.route('/results/house/')
def results_house():
    """
    House big board
    """
    from models import Race

    context = make_context()

    context['page_title'] = 'House'
    context['page_class'] = 'house'
    context['column_number'] = 2

    races = Race.select().where(Race.office_name == 'U.S. House')

    context['poll_groups'] = _group_races_by_closing_time(races[0:60])

    context['bop'] = _calculate_bop(races, HOUSE_MAJORITY, HOUSE_INITIAL_BOP)
    return render_template('slides/congress_results.html', **context)

@app.route('/results/senate/')
def results_senate():
    """
    Senate big board
    """
    from models import Race

    context = make_context()

    context['page_title'] = 'Senate'
    context['page_class'] = 'senate'
    context['column_number'] = 2

    races = Race.select().where(Race.office_name == 'U.S. Senate')

    context['poll_groups'] = _group_races_by_closing_time(races)

    context['bop'] = _calculate_bop(races, SENATE_MAJORITY, SENATE_INITIAL_BOP)

    return render_template('slides/congress_results.html', **context)

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
@cors
def _slide(slug):
    """
    Serve up slide html fragment
    """
    from models import Slide

    slide = Slide.get(Slide.slug == slug)
    return render_template('_slide.html', body=slide.body)

def rotate_slide():
    from models import SlideSequence

    first = SlideSequence.first() or 0

    try:
        with open(STACK_NUMBER_FILENAME, 'r') as f:
            order = int(f.read().strip())
    except IOError:
        order = first

    try:
        next_slide = SlideSequence\
            .select()\
            .where(SlideSequence.order > order)\
            .order_by(SlideSequence.order.asc())\
            .get()
    except SlideSequence.DoesNotExist:
        next_slide = SlideSequence.get(SlideSequence.order==first)

    with open(STACK_NUMBER_FILENAME, 'w') as f:
        f.write(unicode(next_slide.order))

    return next_slide

@app.route('/live-data/next-slide.json')
@cors
def _stack_json():
    """
    Serve up pointer to next slide in stack
    """
    next_slide = rotate_slide()

    js = json.dumps({
        'next': 'slides/%s.html' % next_slide.slide.slug,
    })
    return js, 200, { 'Content-Type': 'application/javascript' }

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
