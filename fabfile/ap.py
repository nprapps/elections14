#!/usr/bin/env python

import json

from fabric.api import task
import requests

import app_config

SECRETS = app_config.get_secrets()

def _get_races(use_cache):
    url = 'https://api.ap.org/v2/init/races/2014-11-04?officeID=S,H,G&format=json'
    cache = {}
    headers = {}

    if use_cache:
        with open('_ap_cache.json') as f:
            cache = json.load(f)

        url = cache['races']['nextrequest']
        headers['If-Modified-Since'] = cache['races']['Last-Modified']
        headers['If-None-Match'] = cache['races']['Etag']

    url += '&apiKey=%s' % SECRETS['AP_API_KEY']
    response = requests.get(url, headers=headers)

    if response.status_code == 304:
        print 'Races already up to date'
        return
    elif response.status_code == 403:
        print 'Rate-limited'
        return
    elif response.status_code != 200:
        print 'Error retrieving races: %i' % response.status_code
        return

    cache['races'] = {
        'nextrequest': response.json()['nextrequest'],
        'Last-Modified': response.headers['Last-Modified'],
        'Etag': response.headers['Etag']
    }

    with open('_ap_cache.json', 'w') as f:
        json.dump(cache, f)

    print 'Updated races'

@task
def bootstrap():
    _get_races(False)

@task
def update():
    _get_races(True)
     
