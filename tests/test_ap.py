#!/usr/bin/env python

import json
import os
import unittest

from fabfile import ap

class APTestCase(unittest.TestCase):
    """
    Tests for the AP scraper.
    """

    def test_init(self):
        """
        Verify race data is properly written to disk
        """

        ap.init('.tests')

        with open('.tests/init_races.json') as f:
            races = json.load(f)
            senate_races = [race for race in races if race['office_id'] == 'S']
            house_races = [race for race in races if race['office_id'] == 'H']
            gov_races = [race for race in races if race['office_id'] == 'G']

            self.assertEqual(len(races), 540)
            self.assertEqual(len(senate_races), 36)
            self.assertEqual(len(house_races), 435)
            self.assertEqual(len(gov_races), 36)


        with open('.tests/init_candidates.json') as f:
            candidates = json.load(f)
            self.assertEqual(len(candidates), 1529)
