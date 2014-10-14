#!/usr/bin/env python

from functools import wraps

from flask import make_response

SENATE_MAJORITY = 51
SENATE_INITIAL_BOP = {
    'dem': 32,
    'gop': 30,
    'other': 2,
}

HOUSE_PAGE_LIMIT = 36
HOUSE_MAJORITY = 218
HOUSE_INITIAL_BOP = {
    'dem': 0,
    'gop': 0,
    'other': 0,
}

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

def group_races_by_closing_time(races):
    """
    Process race results for use in templates.
    """
    results = {}

    for race in races:
        if not results.get(race.poll_closing_time):
            results[race.poll_closing_time] = []

        results[race.poll_closing_time].append(race)

    return sorted(results.items())

def calculate_bop(races, majority, initial):
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
            if race.previous_party:
                bop[race.previous_party]['picked_up'] -= 1

    return bop

def calculate_seats_left(races):
    """
    Calculate seats remaining
    """
    seats = races.count()
    for race in races:
        if race.is_called():
            seats -= 1
    return seats

