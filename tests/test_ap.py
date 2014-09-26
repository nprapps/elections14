#!/usr/bin/env python

import json
import os
import unittest

import responses

from fabfile import ap

class APTestCase(unittest.TestCase):
    """
    Tests for the AP scraper.
    """
    def setUp(self):
        try:
            os.remove(ap.CACHE_FILE)
        except OSError:
            pass

    @responses.activate
    def test_race_init(self):
        """
        Verify race data is cached correctly.
        """
        with open('data/tests/race_init.json') as f:
            body = f.read()

        def responder(request):
            headers = {
                'Last-Modified': 'Fri, 26 Sep 2014 19:56:40 GMT',
                'Etag': '3a401ee1-json'
            }

            return (200, headers, body) 

        responses.add_callback(
            responses.GET,
            'https://api.ap.org/v2/init/races/2014-11-04',
            callback=responder,
            content_type='application/json'
        )

        ap._init_ap('init/races') 

        with open(ap.CACHE_FILE) as f:
            data = json.load(f)

        self.assertIn('init/races', data)

        cache = data['init/races']

        self.assertIn('Etag', cache)
        self.assertIn('Last-Modified', cache)
        self.assertIn('nextrequest', cache)

        response = cache['response']
        
        self.assertEqual(json.loads(body), response)

    @unittest.skip('TODO')
    def test_candidate_init(self):
        pass

    @unittest.skip('TODO')
    def test_race_update(self):
        pass

    @unittest.skip('TODO')
    def test_candidate_update(self):
        pass

    @unittest.skip('TODO')
    def test_write(self):
        """
        Test writing format-neutral intermediaries from AP response cache.
        """
        pass

