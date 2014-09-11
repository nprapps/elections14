#!/usr/bin/env python

import json
import os
from time import sleep

from fabric.api import task
import requests
import slugify

import app_config

SECRETS = app_config.get_secrets()
CACHE_FILE = '.ap_cache.json'

def _init_ap(endpoint):
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
            'officeID': 'S,H,G',
            'format': 'json',
            'apiKey': SECRETS['AP_API_KEY']
        }

    params = {
        'officeID': 'S,H,G',
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

    sleep(30)

def _update_ap(endpoint, use_cache=True):
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
            'officeID': 'S,H,G',
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

    sleep(30)

def _write():
    with open(CACHE_FILE) as f:
        cache = json.load(f)

    races = []
    candidates = []
    all_races = cache['init/races']['response']['races']
    all_candidates = cache['init/candidates']['response']['candidates']

    for race in all_races:
        race_candidates = [{
            'candidate_id': candidate.get('candidateID'),
            'last_name': candidate.get('last'),
            'party': candidate.get('party'),
            'first_name': candidate.get('first'),
            'race_id': race.get('raceID')
        } for candidate in race['candidates']]

        candidates.extend(race_candidates)

        # Init/races does not include state data. We need to look up the state by
        # grabbing one of the candidates and matching to the init/candidates data.
        # This suuuuucks.

        state_candidate = race['candidates'][0]['candidateID']

        for candidate in all_candidates:
            if candidate['candidateID'] == state_candidate:
                statePostal = candidate['statePostal']
                break

        races.append({
            'state_postal': statePostal,
            'office_id': race.get('officeID'),
            'office_name': race.get('officeName'),
            'seat_name': race.get('seatName'),
            'seat_number': race.get('seatNum'),
            'race_id': race.get('raceID'),
            'race_type': race.get('raceTypeID'),
            'last_updated': race.get('lastUpdated'),
        })

    with open('data/races.json', 'w') as f:
        json.dump(races, f)

    with open('data/candidates.json', 'w') as f:
        json.dump(candidates, f)


@task
def init():
    try:
        os.remove(CACHE_FILE)
    except OSError:
        pass

    _init_ap('init/races')
    _init_ap('init/candidates')

@task
def update():
    _update_ap('races')
    _update_ap('calls')

@task
def write():
    _write()
