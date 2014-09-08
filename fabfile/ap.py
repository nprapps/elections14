#!/usr/bin/env python

import json
from time import sleep

from fabric.api import task
import requests

import app_config

SECRETS = app_config.get_secrets()

def _get_ap(endpoint, use_cache=True):
    url = 'https://api.ap.org/v2/init/%s/2014-11-04' % endpoint
    params = {}
    
    with open('_ap_cache.json') as f:
        cache = json.load(f)

    headers = {}

    if use_cache:
        url = cache[endpoint]['nextrequest']
        headers['If-Modified-Since'] = cache[endpoint]['Last-Modified']
        headers['If-None-Match'] = cache[endpoint]['Etag']

        # If using cache, other params have already been added to url
        params = {
            'apiKey': SECRETS['AP_API_KEY']
        }
    else:
        params.update({
            'officeID': 'S,H,G',
            'format': 'json',
            'apiKey': SECRETS['AP_API_KEY']
        })

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
        'nextrequest': response.json()['nextrequest'],
        'Last-Modified': response.headers['Last-Modified'],
        'Etag': response.headers['Etag']
    }

    with open('_ap_cache.json', 'w') as f:
        json.dump(cache, f)

    print '%s: updated' % endpoint

    sleep(30)

@task
def bootstrap():
    _get_ap('races', False)
    _get_ap('candidates', False)

@task
def update():
    _get_ap('races', True)
    _get_ap('candidates', True)
     
