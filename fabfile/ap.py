#!/usr/bin/env python

import json

from fabric.api import task
import requests

import app_config

SECRETS = app_config.get_secrets()

def _get_ap(endpoint, params={}, use_cache=True):
    url = 'https://api.ap.org/v2/init/%s/2014-11-04' % endpoint
    
    cache = {}
    headers = {}

    if use_cache:
        with open('_ap_cache.json') as f:
            cache = json.load(f)

        url = cache[endpoint]['nextrequest']
        headers['If-Modified-Since'] = cache[endpoint]['Last-Modified']
        headers['If-None-Match'] = cache[endpoint]['Etag']

        # If using cache, other params have already been added to url
        params = {
            'apiKey': SECRETS['AP_API_KEY']
        }
    else:
        params.update({
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

@task
def bootstrap():
    _get_ap('races', { 'officeID': 'S,H,G' }, False)

@task
def update():
    _get_ap('races', { 'officeID': 'S,H,G' }, True)
     
