#!/usr/bin/env python

from flask import render_template

from render_utils import make_context

import app_utils

def senate_big_board():
    """
    Senate big board
    """
    from models import Race

    context = make_context()

    context['page_title'] = 'Senate'
    context['page_class'] = 'senate'
    context['column_number'] = 2

    races = Race.select().where(Race.office_name == 'U.S. Senate').order_by(Race.poll_closing_time, Race.state_postal)

    context['poll_groups'] = app_utils.group_races_by_closing_time(races)
    context['bop'] = app_utils.calculate_bop(races, app_utils.SENATE_MAJORITY, app_utils.SENATE_INITIAL_BOP)
    context['not_called'] = app_utils.calculate_seats_left(races)

    return render_template('slides/race_results.html', **context)

def house_big_board(page):
    """
    House big board
    """
    from models import Race

    context = make_context()

    context['page_title'] = 'House Page %s of 2' % page
    context['page_class'] = 'house'
    context['column_number'] = 2

    all_races = Race.select().where(Race.office_name == 'U.S. House')
    all_featured_races = Race.select().where((Race.office_name == 'U.S. House') & (Race.featured_race == True)).order_by(Race.poll_closing_time, Race.state_postal)

    if page == 2:
        featured_races = all_featured_races[app_utils.HOUSE_PAGE_LIMIT:]
    else:
        featured_races = all_featured_races[:app_utils.HOUSE_PAGE_LIMIT]

    context['poll_groups'] = app_utils.group_races_by_closing_time(featured_races)
    context['bop'] = app_utils.calculate_bop(all_races, app_utils.HOUSE_MAJORITY, app_utils.HOUSE_INITIAL_BOP)
    context['not_called'] = app_utils.calculate_seats_left(all_races)
    context['seat_number'] = ".seat_number"

    return render_template('slides/race_results.html', **context)

def house_big_board_one():
    """
    First page of house results.
    """
    return house_big_board(1)

def house_big_board_two():
    """
    Second page of house results.
    """
    return house_big_board(2)

def governor_big_board():
    """
    Governor big board
    """
    from models import Race

    context = make_context()

    context['page_title'] = 'Governors'
    context['page_class'] = 'governor'
    context['column_number'] = 2

    races = Race.select().where(Race.office_name == 'Governor').order_by(Race.poll_closing_time, Race.state_postal)

    context['poll_groups'] = app_utils.group_races_by_closing_time(races)

    return render_template('slides/race_results.html', **context)

def ballot_measures_big_board():
    """
    Governor big board
    """
    from models import Race

    context = make_context()

    context['page_title'] = 'Ballot Measures'
    context['page_class'] = 'ballot-measures'
    context['column_number'] = 2

    races = Race.select().where((Race.office_id == 'I') & (Race.featured_race == True)).order_by(Race.poll_closing_time, Race.state_postal)

    context['poll_groups'] = app_utils.group_races_by_closing_time(races)

    return render_template('slides/ballot_measure_results.html', **context)


def balance_of_power():
    """
    Serve up the balance of power graph
    """

    from models import Race

    context = make_context()

    context['page_title'] = 'Balance of Power'
    context['page_class'] = 'balance-of-power'

    house_races = Race.select().where(Race.office_name == 'U.S. House').order_by(Race.state_postal)
    senate_races = Race.select().where(Race.office_name == 'U.S. Senate').order_by(Race.state_postal)

    context['house_bop'] = app_utils.calculate_bop(house_races, app_utils.HOUSE_MAJORITY, app_utils.HOUSE_INITIAL_BOP)
    context['senate_bop'] = app_utils.calculate_bop(senate_races, app_utils.SENATE_MAJORITY, app_utils.SENATE_INITIAL_BOP)
    context['house_not_called'] = app_utils.calculate_seats_left(house_races)
    context['senate_not_called'] = app_utils.calculate_seats_left(senate_races)

    return render_template('slides/balance-of-power.html', **context)

def blue_dogs():
    """
    Ongoing list of how blue dog democrats are faring
    """
    context = make_context()

    return render_template('slides/blue-dogs.html', **context)

def house_freshmen():
    """
    Ongoing list of how representatives elected in 2012 are faring
    """
    context = make_context()

    return render_template('slides/house-freshmen.html', **context)

def incumbents_lost():
    """
    Ongoing list of which incumbents lost their elections
    """
    context = make_context()

    return render_template('slides/incumbents-lost.html', **context)

def obama_reps():
    """
    Ongoing list of Incumbent Republicans In Districts Barack Obama Won In 2012
    """
    context = make_context()

    return render_template('slides/obama-reps.html', **context)

def poll_closing():
    """
    Serve up poll closing information
    """
    context = make_context()

    return render_template('slides/poll-closing.html', **context)

def rematches():
    """
    List of elections with candidates who have faced off before
    """
    context = make_context()

    return render_template('slides/rematches.html', **context)

def romney_dems():
    """
    Ongoing list of Incumbent Democrats In Districts Mitt Romney Won In 2012
    """
    context = make_context()

    return render_template('slides/romney-dems.html', **context)


