#!/usr/bin/env python

from datetime import datetime
import time
import json
import os
from time import sleep

from fabric.api import task
import requests

import app_config

SLEEP_INTERVAL = 60 
SECRETS = app_config.get_secrets()
CACHE_FILE = '.ap_cache.json'

def _init_ap(endpoint):
    """
    Make a request to an AP init endpoint.
    """
    url = 'https://api.ap.org/v2/%s/2014-11-04' % endpoint
    headers = {}

    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
    except IOError:
        cache = {}

    if endpoint in cache:
        url = cache[endpoint]['nextrequest']
        headers['If-Modified-Since'] = cache[endpoint]['Last-Modified']
        headers['If-None-Match'] = cache[endpoint]['Etag']

        # If using cache, other params have already been added to url
        params = {
            'apiKey': SECRETS['AP_API_KEY']
        }
    else:
        params = {
            'officeID': 'S,H,G,I',
            'format': 'json',
            'apiKey': SECRETS['AP_API_KEY']
        }

    params = {
        'officeID': 'S,H,G,I',
        'format': 'json',
        'apiKey': SECRETS['AP_API_KEY']
    }

    response = requests.get(url, params=params)

    if response.status_code == 304:
        print '%s: already up to date' % endpoint
        return
    elif response.status_code == 403:
        print '%s: rate-limited' % endpoint
        return
    elif response.status_code != 200:
        print '%s: returned %i' % (endpoint, response.status_code)
        return

    cache[endpoint] = {
        'response': response.json(),
        'nextrequest': response.json()['nextrequest'],
        'Last-Modified': response.headers['Last-Modified'],
        'Etag': response.headers['Etag']
    }

    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=4)

    print '%s: inited' % endpoint

def _update_ap(endpoint, use_cache=True):
    """
    Make a request to an AP update endpoint.
    """
    url = 'https://api.ap.org/v2/%s/2014-11-04' % endpoint
    headers = {}

    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
    except IOError:
        cache = {}

    if endpoint in cache:
        url = cache[endpoint]['nextrequest']
        headers['If-Modified-Since'] = cache[endpoint]['Last-Modified']
        headers['If-None-Match'] = cache[endpoint]['Etag']

        # If using cache, other params have already been added to url
        params = {
            'apiKey': SECRETS['AP_API_KEY']
        }
    else:
        params = {
            'officeID': 'S,H,G,I',
            'format': 'json',
            'apiKey': SECRETS['AP_API_KEY']
        }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 304:
        print '%s: already up to date' % endpoint
        return
    elif response.status_code == 403:
        print '%s: rate-limited' % endpoint
        return
    elif response.status_code != 200:
        print '%s: returned %i' % (endpoint, response.status_code)
        return

    cache[endpoint] = {
        'response': response.json(),
        'nextrequest': response.json()['nextrequest'],
        'Last-Modified': response.headers['Last-Modified'],
        'Etag': response.headers['Etag']
    }

    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=4)

    print '%s: updated' % endpoint

@task
def bootstrap():
    init()
    update()

@task
def init(output_dir='data'):
    """
    Initialize data from AP.
    """
    try:
        os.remove(CACHE_FILE)
    except OSError:
        pass

    _init_ap('init/races')
    sleep(SLEEP_INTERVAL)
    _init_ap('init/candidates')

    write_init_races('%s/init_races.json' % output_dir)
    write_init_candidates('%s/init_candidates.json' % output_dir)

@task
def get_incumbents(output_dir='data'):
    """
    Get incumbent data from updates.
    """
    _update_ap('races')

    write_incumbents('%s/incumbents.json' % output_dir)

@task
def update(output_dir='data'):
    """
    Update data from AP.
    """
    _update_ap('races')
    _update_ap('calls')

    write_update('%s/update.json' % output_dir)
    write_calls('%s/calls.json' % output_dir)

def _generate_race_id(obj, state_postal=None):
    """
    Makes an unique compound ID out of statePostal and raceID
    """
    if state_postal:
        return '%s-%s' % (state_postal, obj['raceID'])
    else:
        return '%s-%s' % (obj['statePostal'], obj['raceID'])

def write_init_races(path):
    """
    Write AP data to intermediary files.
    """
    with open(CACHE_FILE) as f:
        cache = json.load(f)

    races = []
    init_races = cache['init/races']['response']['races']

    for race in init_races:
        races.append({
            'state_postal': race.get('statePostal'),
            'office_id': race.get('officeID'),
            'office_name': race.get('officeName'),
            'seat_name': race.get('seatName'),
            'seat_number': race.get('seatNum'),
            'race_id': _generate_race_id(race),
            'race_type': race.get('raceTypeID'),
            'last_updated': race.get('lastUpdated')
        })

    with open(path, 'w') as f:
        json.dump(races, f, indent=4)

def write_init_candidates(path):
    with open(CACHE_FILE) as f:
        cache = json.load(f)

    candidates = []
    init_candidates = cache['init/candidates']['response']['candidates']

    for candidate in init_candidates:
        candidates.append({
            'candidate_id': candidate.get('candidateID'),
            'last_name': candidate.get('last'),
            'party': candidate.get('party'),
            'first_name': candidate.get('first'),
            'race_id': _generate_race_id(candidate)
        })

    with open(path, 'w') as f:
        json.dump(candidates, f, indent=4)

def write_update(path):
    with open(CACHE_FILE) as f:
        cache = json.load(f)

    # Updates
    updates = []
    update_races = cache['races']['response'].get('races', [])

    for race in update_races:
        stateRU = race['reportingUnits'][0]

        assert stateRU.get('level', None) == 'state'

        update = {
            'race_id': _generate_race_id(race, stateRU.get('statePostal')),
            'is_test': race.get('test'),
            'precincts_reporting': stateRU.get('precinctsReporting'),
            'precincts_total': stateRU.get('precinctsTotal'),
            'last_updated': stateRU.get('lastUpdated'),
            'candidates': []
        }

        for candidate in stateRU.get('candidates'):
            update['candidates'].append({
                'candidate_id': candidate.get('candidateID'),
                'vote_count': candidate.get('voteCount')
            })

        updates.append(update)

    with open(path, 'w') as f:
        json.dump(updates, f, indent=4)

def write_calls(path):
    with open(CACHE_FILE) as f:
        cache = json.load(f)
 
    # Calls
    calls = []
    update_calls = cache['calls']['response']['calls']

    for race in update_calls:
        if not race.get('raceID'):
            continue

        call = {
            'race_id': _generate_race_id(race),
            'ap_called_time':race.get('callTimestamp'),
        }

        winners = [candidate for candidate in race.get('candidates') if candidate.get('winner') == 'X']
        runoff_winners = [candidate for candidate in race.get('candidates') if candidate.get('winner') == 'R']

        if len(winners) and len(runoff_winners):
            print 'ERROR: Race has winners and runoff winners! (%s, %s, %s)' % (_generate_race_id(race), race['raceType'], race['statePostal'])
            continue

        if len(winners):
            if len(winners) > 1:
                print 'WARN: Found race with multiple winners! (%s, %s, %s)' % (_generate_race_id(race), race['raceType'], race['statePostal'])
            winner = winners[0]
            call['ap_winner'] = winner['candidateID']

        elif len(runoff_winners):
            call['ap_runoff_winners'] = [candidate['candidateID'] for candidate in runoff_winners]

        calls.append(call)

    with open(path, 'w') as f:
        json.dump(calls, f, indent=4)

def write_incumbents(path):
    """
    Write incumbent data to a file
    """

    with open(CACHE_FILE) as f:
        cache = json.load(f)

    incumbents = []
    races = cache['races']['response'].get('races', [])

    for race in races:
        stateRU = race['reportingUnits'][0]

        assert stateRU.get('level', None) == 'state'

        for candidate in stateRU.get('candidates'):
            incumbents.append({
                'candidate_id': candidate.get('candidateID'),
                'incumbent': candidate.get('incumbent', False)
            })

    with open(path, 'w') as f:
        json.dump(incumbents, f, indent=4)

@task
def record():
    """
    Begin recording AP data for playback later.
    """
    update_interval = 60 * 5 
    folder = datetime.now().strftime('%Y-%m-%d')
    root = 'data/recording/%s' % folder

    if os.path.exists(root):
        print 'ERROR: %s already exists. Delete it if you want to re-record for today!' % root
        return
    else:
        os.mkdir(root)

    while True:
        timestamp = time.time()
        folder = '%s/%s' % (root, timestamp)

        os.mkdir(folder)

        init(folder)
        update(folder)

        sleep(update_interval)

@task
def playback(folder_name='2014-10-06', update_interval=60):
    """
    Begin playback of recorded AP data.
    """
    from fabfile import data

    folder = 'data/recording/%s' % folder_name

    timestamps = sorted(os.listdir(folder))
    initial = '%s/%s' % (folder, timestamps[0])

    for timestamp in timestamps[1:]:
        print '==== LOADING NEXT DATA (%s) ====' % timestamp
        path = '%s/%s' % (folder, timestamp)
        data.load_updates('%s/update.json' % path)
        sleep(int(update_interval))

    print '==== PLAYBACK COMPLETE ===='
