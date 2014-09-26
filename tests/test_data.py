#!/usr/bin/env python

from datetime import datetime
import unittest

from fabfile import data
from models import Race

class DataTestCase(unittest.TestCase):
    """
    Test the data import process.
    """
    def setUp(self):
        data.local_reset_db()
        data.create_tables()
        
    def test_load_races(self):
        """
        Test loading races from intermediary file.
        """
        data.load_races('data/tests/races.json')

        race = Race.select().get()

        self.assertEqual(race.state_postal, 'OR')
        self.assertEqual(race.office_id, 'G')
        self.assertEqual(race.office_name, 'Governor')
        self.assertEqual(race.seat_name, None)
        self.assertEqual(race.seat_number, None)
        self.assertEqual(race.race_id, '38019')
        self.assertEqual(race.race_type, 'G')
        self.assertEqual(race.last_updated, datetime(2014, 9, 18, 20, 6, 28))

    @unittest.skip('TODO')
    def test_load_candidates(self):
        pass

    @unittest.skip('TODO')
    def test_update_results(self):
        pass
