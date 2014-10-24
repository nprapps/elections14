#!/usr/bin/env python

import requests

API_KEY = 'MDExODkwMDg3MDEzNzU0NTY2ODlmYWY0Yw001'
MAX_STATION_ID = 1466

def main():
    for station_id in range(0, 1466 + 1):
        print station_id

        response = requests.get('http://api.npr.org/stations', params={
            'id': station_id,
            'apiKey': API_KEY,
            'format': 'json'
        })

        data = response.json()

        if 'station' not in data:
            print 'Error: %s' % data['message']['id']

        with open('api_requests/%i.json' % station_id, 'w') as w:
            w.write(response.text.encode('utf-8'))
    
if __name__ == '__main__':
    main()
