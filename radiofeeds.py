#!/usr/bin/env python

from ConfigParser import ConfigParser
from glob import glob
import json
from StringIO import StringIO

import requests

def main():
    streams = {}

    for path in glob('station_responses/*.json'):
        with open(path) as f:
            data = json.load(f)

            if not data['station'][0]:
                print 'No station'
                continue

            station = data['station'][0]

            print station['name']['$text']

            if not station['callLetters']:
                print 'No callsign'
                continue

            callsign = station['callLetters']['$text']

            if 'url' not in station:
                print 'No urls'
                continue

            for url in station['url']:
                if url['typeId'] == '10':
                    playlist_url = url['$text']
                    break

            if not playlist_url:
                print 'No stream'
                continue

            if callsign in streams:
                print 'Duplicate callsign'

            print playlist_url

            response = requests.get(playlist_url, timeout=5)

            if response.status_code != 200:
                print 'Failed to get playlist'
                continue

            if playlist_url.endswith('.m3u'):
                stream_url = parse_m3u(response.text)
            elif playlist_url.endswidth('.pls'):
                stream_url = parse_pls(response.text)
            else:
                print 'Unknown playlist format: %s' % playlist_url
                continue

            if not stream_url:
                print 'Unable to parse stream url.'
                continue

            streams[callsign] = stream_url 

            print stream_url
            
def parse_m3u(data):
    lines = StringIO(data)

    for line in lines:
        if not line.startswith('#'):
            return line

    return None

def parse_pls(data):
    lines = StringIO(data)

    config = ConfigParser()
    config.readfp(lines)

    return config.get('playlist', 'File1')

if __name__ == '__main__':
    main()
