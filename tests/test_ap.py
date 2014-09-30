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

    @responses.activate
    def test_candidate_init(self):
        """
        Verify candidate data is cached correctly.
        """
        with open('data/tests/candidates_init.json') as f:
            body = f.read()

        def responder(request):
            headers = {
                'Last-Modified': 'Tue, 30 Sep 2014 15:08:31 GMT', 
                'Etag': '40b13862-json'
            }

            return (200, headers, body) 

        responses.add_callback(
            responses.GET,
            'https://api.ap.org/v2/init/candidates/2014-11-04',
            callback=responder,
            content_type='application/json'
        )

        ap._init_ap('init/candidates') 

        with open(ap.CACHE_FILE) as f:
            data = json.load(f)

        self.assertIn('init/candidates', data)

        cache = data['init/candidates']

        self.assertIn('Etag', cache)
        self.assertIn('Last-Modified', cache)
        self.assertIn('nextrequest', cache)

        response = cache['response']
       
        self.assertEqual(json.loads(body), response)

    @responses.activate
    def test_race_update(self):
        """
        Verify race update data is cached correctly.
        """
        with open('data/tests/race_update.json') as f:
            body = f.read()

        def responder(request):
            headers = {
                'Last-Modified': 'Tue, 30 Sep 2014 15:18:50 GMT', 
                'Etag': 'ffffffffbb1db2cd-json'
            }

            return (200, headers, body) 

        responses.add_callback(
            responses.GET,
            'https://api.ap.org/v2/races/2014-11-04',
            callback=responder,
            content_type='application/json'
        )

        ap._update_ap('races') 

        with open(ap.CACHE_FILE) as f:
            data = json.load(f)

        self.assertIn('races', data)

        cache = data['races']

        self.assertIn('Etag', cache)
        self.assertIn('Last-Modified', cache)
        self.assertIn('nextrequest', cache)

        response = cache['response']
       
        self.assertEqual(json.loads(body), response)


    @unittest.skip('TODO')
    def test_candidate_update(self):
        pass

    @unittest.skip('TODO')
    def test_write(self):
        """
        Test writing format-neutral intermediaries from AP response cache.
        """
        pass

