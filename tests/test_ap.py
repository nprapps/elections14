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
        with open('data/tests/ap_init_races.json') as f:
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
        with open('data/tests/ap_init_candidates.json') as f:
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
        with open('data/tests/ap_update.json') as f:
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

    @responses.activate
    def test_calls_update(self):
        """
        Verify calls update data is cached correctly.
        """
        with open('data/tests/ap_calls.json') as f:
            body = f.read()

        def responder(request):
            headers = {
                'Last-Modified': 'Thu, 25 Sep 2014 18:10:54 GMT',
                'Etag': '\"ffffffffa71c73ab-json\"'
            }

            return (200, headers, body)

        responses.add_callback(
            responses.GET,
            'https://api.ap.org/v2/calls/2014-11-04',
            callback=responder,
            content_type='application/json'
        )

        ap._update_ap('calls')

        with open(ap.CACHE_FILE) as f:
            data = json.load(f)

        self.assertIn('calls', data)

        cache = data['calls']

        self.assertIn('Etag', cache)
        self.assertIn('Last-Modified', cache)
        self.assertIn('nextrequest', cache)

        response = cache['response']

        self.assertEqual(json.loads(body), response)

    def test_write(self):
        """
        Test writing format-neutral intermediaries from AP response cache.
        """
        ap_cache = {}
        ap_cache['init/races'] = {}
        ap_cache['init/candidates'] = {}
        ap_cache['races'] = {}

        with open('data/tests/ap_init_races.json') as f:
            test_races = json.load(f)
            ap_cache['init/races']['response'] = test_races

        with open('data/tests/ap_init_candidates.json') as f:
            test_candidates = json.load(f)
            ap_cache['init/candidates']['response'] = test_candidates

        with open('data/tests/ap_update.json') as f:
            test_updates = json.load(f)
            ap_cache['races']['response'] = test_updates

        with open('data/tests/ap_calls.json') as f:
            test_calls = json.load(f)
            ap_cache['calls']['response'] = test_updates

        with open('.ap_cache.json', 'w') as f:
            f.write(json.dumps(ap_cache))

        ap.write(output_dir='.tests')

        with open('.tests/init_races.json') as f:
            written_races = json.load(f)

            init_race = test_races['races'][0]
            written_race = written_races[0]

            self.assertEqual(init_race['raceTypeID'], written_race['race_type'])
            self.assertEqual(init_race['statePostal'], written_race['state_postal'])
            self.assertEqual(init_race['raceID'], written_race['race_id'])
            self.assertEqual(init_race['officeName'], written_race['office_name'])
            self.assertEqual(init_race['seatNum'], written_race['seat_number'])
            self.assertEqual(init_race['lastUpdated'], written_race['last_updated'])
            self.assertEqual(init_race['seatName'], written_race['seat_name'])
            self.assertEqual(init_race['officeID'], written_race['office_id'])

        with open('.tests/init_candidates.json') as f:
            written_candidates = json.load(f)

            init_candidates = test_candidates['candidates']

            for i, init_candidate in enumerate(init_candidates):
                self.assertEqual(init_candidate['party'], written_candidates[i]['party'])
                self.assertEqual(init_candidate['first'], written_candidates[i]['first_name'])
                self.assertEqual(init_candidate['last'], written_candidates[i]['last_name'])
                self.assertEqual(init_candidate['candidateID'], written_candidates[i]['candidate_id'])
                self.assertEqual(init_candidate['raceID'], written_candidates[i]['race_id'])

        with open('.tests/update.json') as f:
            written_updates = json.load(f)

            updates = test_updates['races']

            for i, update in enumerate(updates):
                ru = update['reportingUnits'][0]

                self.assertEqual(update['raceID'], written_updates[i]['race_id'])
                self.assertEqual(update['test'], written_updates[i]['is_test'])
                self.assertEqual(ru['precinctsReporting'], written_updates[i]['precincts_reporting'])
                self.assertEqual(ru['lastUpdated'], written_updates[i]['last_updated'])
                self.assertEqual(ru['precinctsTotal'], written_updates[i]['precincts_total'])

                for j, candidate in enumerate(ru['candidates']):
                    written_candidate = written_updates[i]['candidates'][j]

                    self.assertEqual(candidate['candidateID'], written_candidate['candidate_id'])
                    self.assertEqual(candidate['voteCount'], written_candidate['vote_count'])
                    
                    if 'winner' in candidate:
                        self.assertEqual(True, written_candidate['ap_winner'])
                    else:
                        self.assertEqual(False, written_candidate['ap_winner'])

        with open('.tests/calls.json') as f:
            written_calls = json.load(f)

            calls = test_calls['calls']

            self.assertEqual(calls[0]['raceID'], written_calls[0]['race_id'])
            self.assertEqual(calls[0]['callTimestamp'], written_calls[0]['ap_called_time'])
