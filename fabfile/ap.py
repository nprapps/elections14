#!/usr/bin/env python

from datetime import datetime, date
import time
import json
import os
from time import sleep

from fabric.api import task
import requests

import app_config

from elections import AP

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
    client = AP(SECRETS['AP_FTP_USER'], SECRETS['AP_FTP_PASSWORD'])
    ticket = client.get_topofticket('2014-11-04')

    races = []
    candidates = []

    for race in ticket.races:
        races.append(process_race(race))
        for candidate in race.candidates:
            candidates.append(process_candidate(candidate))

    with open('%s/init_races.json' % output_dir, 'w') as f:
        json.dump(races, f, indent=4)

    with open('%s/init_candidates.json' % output_dir, 'w') as f:
        json.dump(candidates, f, indent=4)

@task
def update(output_dir='data'):
    """
    Update data from AP.
    """
    client = AP(SECRETS['AP_FTP_USER'], SECRETS['AP_FTP_PASSWORD'])
    ticket = client.get_topofticket('2014-11-04')

    write_update(ticket, '%s/update.json' % output_dir)
    write_calls(ticket, '%s/calls.json' % output_dir)


def process_race(race):
    """
    Process a single race into our intermediary format.
    """
    ret = {
        'state_postal': race.state_postal,
        'office_id': race.office_id,
        'office_name': race.office_name,
        'seat_name': race.seat_name,
        'seat_number': race.seat_number,
        'race_id': race.ap_race_number,
        'race_type': race.race_type,
        #'last_updated': race.get('lastUpdated') # This doesn't exist in race object in FTP
    }
    return ret

def process_candidate(candidate):
    """
    Process a single candidate into our intermediary format.
    """
    ret = {
        'candidate_id': candidate.ap_natl_number,
        'first_name': candidate.first_name,
        'last_name': candidate.last_name,
        'race_id': candidate.ap_race_number,
        'party': candidate.party,
        'incumbent': candidate.is_incumbent,
    }
    return ret

def write_update(ticket, path):
    """
    Write an update
    """
    updates = []

    for race in ticket.races:
        update = {
            'race_id': race.ap_race_number,
            'precincts_reporting': 0,
            'precincts_total': 0,
            'candidates': [],
        }

        for ru in race.reporting_units:
            update['precincts_total'] += ru.precincts_total
            if ru.precincts_reporting:
                update['precincts_reporting'] += ru.precincts_reporting

        for candidate in race.candidates:
            update['candidates'].append({
                'candidate_id': candidate.ap_natl_number,
                'vote_count': candidate.vote_total
            })

        updates.append(update)

    with open(path, 'w') as f:
        json.dump(updates, f, indent=4)

def write_calls(ticket, path):
    """
    Write call data to disk
    """
    new_calls = []
    called_ids = []

    mod_string = ticket.client.ftp.sendcmd('MDTM %s' % ticket.results_file_path)
    mod_time = datetime.strptime(mod_string[4:], '%Y%m%d%H%M%S')

    if os.path.isfile(path):
        with open(path) as f:
            previous_calls = json.load(f)
            called_ids = [call.get('race_id') for call in previous_calls]

    for race in ticket.races:
        if race.ap_race_number not in called_ids:
            winners = [candidate for candidate in race.candidates if candidate.is_winner]

            if len(winners) > 1:
                print 'WARN: Found race with multiple winners! (%s, %s, %s)' % (race.ap_race_number, race.race_type, race.state_postal)

            if len(winners):
                winner = winners[0]
                new_calls.append({
                    'race_id': race.ap_race_number,
                    'ap_winner': winner.ap_natl_number,
                    'ap_called_time': datetime.strftime(mod_time, '%Y-%m-%dT%H:%M:%SZ'),
                })

        else:
            print "Skipped %s, already called" % race.ap_race_number

    calls = previous_calls + new_calls

    with open(path, 'w') as f:
        json.dump(calls, f, indent=4)

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
        print "Writing to %s" % folder

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
