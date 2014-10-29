#!/usr/bin/env python

import json
import os
import unittest

from app_config import STATES
from fabfile import ap

NUM_RACES = 541
NUM_SENATE_RACES = 36
NUM_HOUSE_RACES = 435
NUM_GOV_RACES = 36
NUM_CANDIDATES = 1530

class APTestCase(unittest.TestCase):
    """
    Tests for the AP scraper.
    """

    def test_init_races(self):
        """
        Verify race data is properly written to disk
        """
        ap.init('.tests')

        with open('.tests/init_races.json') as f:
            races = json.load(f)
            senate_races = [race for race in races if race['office_id'] == 'S']
            house_races = [race for race in races if race['office_id'] == 'H']
            gov_races = [race for race in races if race['office_id'] == 'G']

            # Correct number of races initialized, fixed #s like Senate Races are
            # particularly useful for testing.
            self.assertEqual(NUM_RACES, len(races))
            self.assertEqual(NUM_SENATE_RACES, len(senate_races))
            self.assertEqual(NUM_HOUSE_RACES, len(house_races))
            self.assertEqual(NUM_GOV_RACES, len(gov_races))

            # Are keys correct?
            expected_keys = [
                'office_name',
                'seat_name',
                'seat_number',
                'race_type',
                'office_id',
                'state_postal',
                'race_id',
            ]
            self.assertItemsEqual(races[0], expected_keys)

            # Are there weird or missing states?
            for race in races:
                self.assertIn(race.get('state_postal'), STATES.keys())

    def test_init_candidates(self):
        """
        Verify candidate data is properly written to disk
        """
        ap.init('.tests')

        with open('.tests/init_candidates.json') as f:
            candidates = json.load(f)

            # Correct number of candidates
            self.assertEqual(len(candidates), NUM_CANDIDATES)

            # Correct keys
            expected_keys = [
                'first_name',
                'last_name',
                'incumbent',
                'candidate_id',
                'race_id',
                'party',
            ]
            self.assertItemsEqual(candidates[0], expected_keys)

    def test_update(self):
        """
        Test writing updates to disk
        """
        ap.update('.tests')

        with open('.tests/update.json') as f:
            races = json.load(f)

            # Correct number of races updated
            self.assertEqual(NUM_RACES, len(races))

            # Keys are correct
            expected_keys = [
                'candidates',
                'race_id',
                'precincts_reporting',
                'precincts_total',
            ]
            self.assertItemsEqual(expected_keys, races[0].keys())


    def test_calls(self):
        """
        Test writing calls to disk
        """

        # @TODO what's the right test here?
        pass
