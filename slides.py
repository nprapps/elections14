#!/usr/bin/env python

from datetime import datetime, timedelta
import json

from dateutil.parser import parse
from flask import render_template
import pytz

from app_utils import *
from render_utils import make_context

def senate_big_board():
    """
    Senate big board
    """
    from models import Race

    races = Race.select().where(Race.office_name == 'U.S. Senate').order_by(Race.poll_closing_time, Race.state_postal)

    timestamp = get_last_updated(races)
    context = make_context(timestamp=timestamp)

    context['page_title'] = 'Senate'
    context['page_class'] = 'senate'

    context['poll_groups'] = columnize_races(races, 19)
    context['bop'] = calculate_bop(races, SENATE_INITIAL_BOP)
    context['not_called'] = calculate_seats_left(races)

    return render_template('slides/race_results.html', **context)

def house_big_board(page):
    """
    House big board
    """
    from models import Race

    all_races = Race.select().where(Race.office_name == 'U.S. House')
    all_featured_races = Race.select().where((Race.office_name == 'U.S. House') & (Race.featured_race == True)).order_by(Race.poll_closing_time, Race.state_postal, Race.seat_number)

    timestamp = get_last_updated(all_races)
    context = make_context(timestamp=timestamp)

    context['page_title'] = 'House'
    context['current_page'] = page
    context['page_class'] = 'house'


    if page == 2:
        featured_races = all_featured_races[HOUSE_PAGE_LIMIT:]
    else:
        featured_races = all_featured_races[:HOUSE_PAGE_LIMIT]

    context['poll_groups'] = columnize_races(featured_races)
    context['bop'] = calculate_bop(all_races, HOUSE_INITIAL_BOP)
    context['not_called'] = calculate_seats_left(all_races)
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

    races = Race.select().where(Race.office_name == 'Governor').order_by(Race.poll_closing_time, Race.state_postal)
    timestamp = get_last_updated(races)

    context = make_context(timestamp=timestamp)

    context['page_title'] = 'Governors'
    context['page_class'] = 'governor'


    context['poll_groups'] = columnize_races(races, 17)

    return render_template('slides/race_results.html', **context)

def ballot_measures_big_board():
    """
    Governor big board
    """
    from models import Race

    races = Race.select().where((Race.office_id == 'I') & (Race.featured_race == True))\
        .order_by(Race.poll_closing_time, Race.state_postal)
    timestamp = get_last_updated(races)
    context = make_context(timestamp=timestamp)

    context['page_title'] = 'Ballot Measures'
    context['page_class'] = 'ballot-measures'

    context['poll_groups'] = columnize_races(races, 9)

    return render_template('slides/ballot_measure_results.html', **context)

def _format_tumblr_date(post):
    # Parse GMT date from API
    post_date = parse(post['date'])

    # Convert to Eastern time (EDT or EST)
    eastern = pytz.timezone('US/Eastern')

    return post_date.astimezone(eastern).strftime('%I:%M %p EST')

def tumblr_text(data):
    post = json.loads(data)

    context = make_context()
    context['post'] = post
    context['formatted_date'] = _format_tumblr_date(post)

    return render_template('slides/tumblr_text.html', **context)

def tumblr_photo(data):
    post = json.loads(data)

    context = make_context()
    context['post'] = post
    context['formatted_date'] = _format_tumblr_date(post)

    image = None

    for size in post['photos'][0]['alt_sizes']:
        if not image or size['width'] > image['width']:
            if size['width'] < 960:
                image = size

    context['image'] = image

    return render_template('slides/tumblr_photo.html', **context)

def tumblr_quote(data):
    post = json.loads(data)

    context = make_context()
    context['post'] = post
    context['formatted_date'] = _format_tumblr_date(post)

    return render_template('slides/tumblr_quote.html', **context)

def _get_recently_called(office_name):
    """
    Get recently called races for a given office.
    """
    from models import Race

    now = datetime.utcnow()
    then = now - timedelta(minutes=15)

    recently_called = []

    for race in Race.select():
        if race.office_name != office_name:
            continue

        if not race.is_called():
            continue

        if not race.get_called_time() >= then:
            continue

        recently_called.append(race)

    return recently_called

def recent_senate_calls():
    """
    Get the most recent called Senate races
    """
    from models import Race
    context = make_context()

    races = Race.recently_called().where(Race.office_name == 'U.S. Senate')

    if not races.count():
        return "no recently called senate races", 404

    context['races'] = races
    context['label'] = 'Senate'

    return render_template('slides/recent-calls.html', **context)

def recent_governor_calls():
    """
    Get the most recent called Governor races
    """
    from models import Race
    context = make_context()

    races = Race.recently_called().where(Race.office_name == 'Governor')

    if not races.count():
        return "no recently called governor races", 404

    context['races'] = races
    context['label'] = 'Governor'

    return render_template('slides/recent-calls.html', **context)

def balance_of_power():
    """
    Serve up the balance of power graph
    """
    from models import Race

    house_races = Race.select().where(Race.office_name == 'U.S. House').order_by(Race.state_postal)
    senate_races = Race.select().where(Race.office_name == 'U.S. Senate').order_by(Race.state_postal)

    senate_updated = get_last_updated(senate_races)
    house_updated = get_last_updated(house_races)
    if senate_updated > house_updated:
        last_updated = senate_updated
    else:
        last_updated = house_updated

    context = make_context(timestamp=last_updated)

    context['page_title'] = 'Balance of Power'
    context['page_class'] = 'balance-of-power'

    context['house_bop'] = calculate_bop(house_races, HOUSE_INITIAL_BOP)
    context['senate_bop'] = calculate_bop(senate_races, SENATE_INITIAL_BOP)
    context['house_not_called'] = calculate_seats_left(house_races)
    context['senate_not_called'] = calculate_seats_left(senate_races)

    return render_template('slides/balance-of-power.html', **context)

def house_freshmen():
    """
    Ongoing list of how representatives elected in 2012 are faring
    """
    from models import Race

    races = Race.select().where(Race.freshmen == True)\
            .order_by(Race.state_postal, Race.seat_number)
    timestamp = get_last_updated(races)
    context = make_context()

    won = [race for race in races if race.is_called() and not race.is_runoff() and not race.party_changed()]
    lost = [race for race in races if race.is_called() and not race.is_runoff() and race.party_changed()]
    not_called = [race for race in races if not race.is_called() or race.is_runoff()]

    context['races_won'] = columnize_card(won, 6)
    context['races_lost'] = columnize_card(lost, 6)
    context['races_not_called'] = columnize_card(not_called, 6)

    context['races_won_count'] = len(won)
    context['races_lost_count'] = len(lost)
    context['races_not_called_count'] = len(not_called)
    context['races_count'] = races.count()

    return render_template('slides/house-freshmen.html', **context)

def incumbents_lost():
    """
    Ongoing list of which incumbents lost their elections
    """

    from models import Race

    called_senate_races = Race.select().where(
        (Race.office_name == 'U.S. Senate') &
        (((Race.ap_called == True) & (Race.accept_ap_call == True)) |
        (Race.npr_called == True))
    ).order_by(Race.state_postal, Race.seat_number)
    called_house_races = Race.select().where(
        (Race.office_name == 'U.S. House') &
        (((Race.ap_called == True) & (Race.accept_ap_call == True)) |
        (Race.npr_called == True))
    ).order_by(Race.state_postal, Race.seat_number)

    senate_incumbents_lost = []
    house_incumbents_lost = []

    senate_updated = get_last_updated(called_senate_races)
    house_updated = get_last_updated(called_house_races)
    if senate_updated > house_updated:
        last_updated = senate_updated
    else:
        last_updated = house_updated

    context = make_context(timestamp=last_updated)

    for race in called_senate_races:
        for candidate in race.candidates:
            if candidate.incumbent and not candidate.is_winner():
                senate_incumbents_lost.append(race)

    for race in called_house_races:
        if not race.is_runoff():
            for candidate in race.candidates:
                if candidate.incumbent and not candidate.is_winner():
                    house_incumbents_lost.append(race)

    context['senate_incumbents_lost_count'] = len(senate_incumbents_lost)
    context['house_incumbents_lost_count'] = len(house_incumbents_lost)

    context['senate_incumbents_lost'] = columnize_card(senate_incumbents_lost, 6)
    context['house_incumbents_lost'] = columnize_card(house_incumbents_lost, 6)

    return render_template('slides/incumbents-lost.html', **context)

def obama_reps():
    """
    Ongoing list of Incumbent Republicans In Districts Barack Obama Won In 2012
    """
    from models import Race

    races = Race.select().where(Race.obama_gop == True).order_by(Race.state_postal, Race.seat_number)
    timestamp = get_last_updated(races)

    context = make_context(timestamp=timestamp)

    won = [race for race in races if race.is_called() and not race.is_runoff() and not race.party_changed()]
    lost = [race for race in races if race.is_called() and not race.is_runoff() and race.party_changed()]
    not_called = [race for race in races if not race.is_called() or race.is_runoff()]

    context['races_won'] = columnize_card(won)
    context['races_lost'] = columnize_card(lost)
    context['races_not_called'] = columnize_card(not_called)

    context['races_won_count'] = len(won)
    context['races_lost_count'] = len(lost)
    context['races_not_called_count'] = len(not_called)
    context['races_count'] = races.count()

    return render_template('slides/obama-reps.html', **context)

def poll_closing():
    """
    Serve up poll closing information
    """
    from models import Race

    # get featured house/ballot measures + all senate and governors
    featured_races = Race.select().where(
        (Race.featured_race == True) |
        (Race.office_name == 'U.S. Senate') |
        (Race.office_name == 'Governor')
    ).order_by(Race.poll_closing_time, Race.state_postal)

    timestamp = get_last_updated(featured_races)

    context = make_context(timestamp=timestamp)

    poll_groups = group_races_by_closing_time(featured_races)

    now = datetime.now()
    for closing_time, races in poll_groups:
        if now < closing_time:
            nearest_closing_time = closing_time
            nearest_poll_group = races
            break

    states_closing = []
    for race in nearest_poll_group:
        states_closing.append(race.state_postal)

    states_closing = set(states_closing)
    context['num_states_closing'] = len(states_closing)

    context['closing_time'] = nearest_closing_time.strftime('%H:%M %p ET')
    context['races'] = nearest_poll_group

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
    from models import Race

    races = Race.select().where(
        (Race.romney_dem == True) &
        (Race.office_name == 'U.S. House')
    ).order_by(Race.state_postal, Race.seat_number)

    timestamp = get_last_updated(races)

    context = make_context(timestamp=timestamp)

    won = [race for race in races if race.is_called() and not race.is_runoff() and not race.party_changed()]
    lost = [race for race in races if race.is_called() and not race.is_runoff() and race.party_changed()]
    not_called = [race for race in races if not race.is_called() or race.is_runoff()]

    context['races_won'] = columnize_card(won)
    context['races_lost'] = columnize_card(lost)
    context['races_not_called'] = columnize_card(not_called)

    context['races_won_count'] = len(won)
    context['races_lost_count'] = len(lost)
    context['races_not_called_count'] = len(not_called)
    context['races_count'] = races.count()


    return render_template('slides/romney-dems.html', **context)

def romney_senate_dems():
    """
    Ongoing list of Democratically-held seats in states Mitt Romney Won In 2012
    """
    from models import Race

    races = Race.select().where(
        (Race.romney_dem == True) &
        (Race.office_name == 'U.S. Senate')
    ).order_by(Race.state_postal, Race.seat_number)

    timestamp = get_last_updated(races)

    context = make_context(timestamp=timestamp)

    won = [race for race in races if race.is_called() and not race.is_runoff() and not race.party_changed()]
    lost = [race for race in races if race.is_called() and not race.is_runoff() and race.party_changed()]
    not_called = [race for race in races if not race.is_called() or race.is_runoff()]

    context['races_won'] = columnize_card(won)
    context['races_lost'] = columnize_card(lost)
    context['races_not_called'] = columnize_card(not_called)

    context['races_won_count'] = len(won)
    context['races_lost_count'] = len(lost)
    context['races_not_called_count'] = len(not_called)
    context['races_count'] = races.count()

    return render_template('slides/romney-senate-dems.html', **context)

