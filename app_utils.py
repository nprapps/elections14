#!/usr/bin/env python

from copy import deepcopy

from decimal import Decimal, InvalidOperation
from functools import wraps
from flask import make_response

SENATE_INITIAL_BOP = {
    'dem': {
        'has': 32,
        'needs': 18,
        'picked_up': 0,
    },
    'gop': {
        'has': 30,
        'needs': 21,
        'picked_up': 0,
    },
    'other': {
        'has': 2,
        'needs': 49,
        'picked_up': 0,
    },
}

HOUSE_PAGE_LIMIT = 36
HOUSE_INITIAL_BOP = {
    'dem': {
        'has': 0,
        'needs': 218,
        'picked_up': 0,
    },
    'gop': {
        'has': 0,
        'needs': 218,
        'picked_up': 0,
    },
    'other': {
        'has': 0,
        'needs': 218,
        'picked_up': 0,
    },
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

def calculate_bop(races, initial_bop):
    """
    Calculate a balance of power
    """
    bop = deepcopy(initial_bop)

    winning_races = [race for race in races if race.is_called() and not race.is_runoff()]

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

def _percent(dividend, divisor):
    try:
        return (Decimal(dividend) / Decimal(divisor)) * 100
    except InvalidOperation:
        return 0

def calculate_state_bop(races):
    current_gop_number = 0
    current_dem_number = 0
    current_other_number = 0
    called_gop_number = 0
    called_dem_number = 0
    called_other_number = 0
    for race in races:
        if race.previous_party == 'gop':
            current_gop_number += 1
        elif race.previous_party == 'dem':
            current_dem_number += 1
        elif race.previous_party == 'other':
            current_other_number += 1

        if race.is_called():
            if race.get_winning_party() == 'gop':
                called_gop_number += 1
            elif race.get_winning_party() == 'dem':
                called_dem_number += 1
            elif race.get_winning_party() == 'other':
                called_other_number += 1

    current_total = current_gop_number + current_dem_number + current_other_number
    current_gop_percent = _percent(current_gop_number, current_total)
    current_dem_percent = _percent(current_dem_number, current_total)
    current_other_percent = _percent(current_other_number, current_total)

    called_total = called_gop_number + called_dem_number + called_other_number
    called_gop_percent = _percent(called_gop_number, called_total)
    called_dem_percent = _percent(called_dem_number, called_total)
    called_other_percent = _percent(called_other_number, called_total)

    return {
        'current_gop_number': current_gop_number,
        'current_dem_number': current_dem_number,
        'current_other_number': current_other_number,
        'current_gop_percent': current_gop_percent,
        'current_dem_percent': current_dem_percent,
        'current_other_percent': current_other_percent,
        'called_gop_number': called_gop_number,
        'called_dem_number': called_dem_number,
        'called_other_number': called_other_number,
        'called_gop_percent': called_gop_percent,
        'called_dem_percent': called_dem_percent,
        'called_other_percent': called_other_percent,
    }

def get_last_updated(races):
    """
    Get latest update time from races
    """
    from models import Race
    races = races.clone()
    try:
        last = races.order_by(Race.last_updated.desc()).limit(1).get()
    except Race.DoesNotExist:
        last = Race.select().order_by(Race.last_updated).limit(1).get()

    return last.last_updated
