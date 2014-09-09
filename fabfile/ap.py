#!/usr/bin/env python

import json
import os
from time import sleep

from fabric.api import task
import requests

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

def _write(endpoint):
    with open(CACHE_FILE) as f:
        cache = json.load(f)

    cleaned_data = []
    all_races = cache[endpoint]['response']['races']

    for race in all_races:
        candidates = [{
            'candidateID': candidate.get('candidateID', ''),
            'last': candidate.get('last', ''),
            'party': candidate.get('party', ''),
            'first': candidate.get('first', ''),
        } for candidate in race['candidates']]

        cleaned_data.append({
            'seatNum': race.get('seatNum', ''),
            'raceID': race.get('raceID', ''),
            'officeName': race.get('officeName', ''),
            'lastUpdated': race.get('lastUpdated', ''),
            'officeID': race.get('officeID', ''),
            'seatName': race.get('seatName', ''),
            'candidates': candidates,
        })

        print cleaned_data

        with open('www/live-data/ap-init.json', 'w') as f:
            json.dump(cleaned_data, f)


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
    _write('init/races')
