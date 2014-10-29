#!/usr/bin/env python

from datetime import datetime
from decimal import Decimal
import unittest

from peewee import *
from playhouse.test_utils import test_database

from fabfile import data
from models import Race, Candidate

test_db = PostgresqlDatabase('elections14test')

class DataTestCase(unittest.TestCase):
    """
    Test the data import process.
    """
    def test_load_races(self):
        """
        Test loading races from intermediary file.
        """
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')

            race = Race.get(Race.race_id == '38529-OR')

            self.assertEqual(race.state_postal, 'OR')
            self.assertEqual(race.office_id, 'H')
            self.assertEqual(race.office_name, 'U.S. House')
            self.assertEqual(race.seat_name, "District 2")
            self.assertEqual(race.seat_number, 2)
            self.assertEqual(race.race_id, '38529-OR')
            self.assertEqual(race.race_type, 'G')

    def test_load_candidates(self):
        with test_database(test_db, [Race, Candidate]):
            data.load_races('data/tests/init_races.json')
            data.load_candidates('data/tests/init_candidates.json')

            candidate = Candidate.select().get()

            self.assertEqual(candidate.first_name, 'Aelea')
            self.assertEqual(candidate.last_name, 'Christofferson')
            self.assertEqual(candidate.party, 'Dem')
            self.assertIsNotNone(candidate.race)
            self.assertEqual(candidate.candidate_id, '4848-OR')

    def test_update_results(self):
        with test_database(test_db, [Race, Candidate]):
            data.load_races('data/tests/init_races.json')
            data.load_candidates('data/tests/init_candidates.json')
            data.load_updates('data/tests/update.json')
            race = Race.get(Race.race_id == '38529-OR')

            candidate_4848 = Candidate.get(Candidate.candidate_id == '4848-OR')
            candidate_4642 = Candidate.get(Candidate.candidate_id == '4642-OR')
            candidate_4979 = Candidate.get(Candidate.candidate_id == '4979-OR')

            self.assertEqual(race.precincts_reporting, 1970)
            self.assertEqual(race.precincts_total, 2288)
            self.assertTrue(race.is_reporting())

            self.assertEqual(candidate_4848.vote_count, 150000)
            self.assertEqual(candidate_4642.vote_count, 200000)
            self.assertEqual(candidate_4979.vote_count, 250000)
            self.assertEqual(race.count_votes(), 600000)

            self.assertEqual(candidate_4848.vote_percent(), Decimal('25.0')) 
            self.assertAlmostEqual(candidate_4642.vote_percent(), Decimal('33.333'), 3) 
            self.assertAlmostEqual(candidate_4979.vote_percent(), Decimal('41.667'), 3) 

            # Results does not call races
            self.assertFalse(candidate_4848.ap_winner)
            self.assertFalse(candidate_4642.ap_winner)
            self.assertFalse(candidate_4979.ap_winner)

    def test_update_calls(self):
        with test_database(test_db, [Race, Candidate]):
            data.load_races('data/tests/init_races.json')
            data.load_candidates('data/tests/init_candidates.json')
            data.load_calls('data/tests/calls.json')

            race = Race.get(Race.race_id == '38529-OR')
            candidate_4848 = Candidate.get(Candidate.candidate_id == '4848')
            candidate_4642 = Candidate.get(Candidate.candidate_id == '4642')
            candidate_4979 = Candidate.get(Candidate.candidate_id == '4979')

            self.assertTrue(race.is_called())
            self.assertTrue(race.ap_called)
            self.assertEqual(race.ap_called_time, datetime(2014, 9, 25, 17, 8, 14))
            self.assertEqual(race.get_called_time(), datetime(2014, 9, 25, 17, 8, 14))

            self.assertFalse(candidate_4848.ap_winner)
            self.assertFalse(candidate_4642.ap_winner)
            self.assertTrue(candidate_4979.ap_winner)

    def test_closing_times(self):
        with test_database(test_db, [Race,]):
            data.load_races('data/tests/init_races.json')
            data.load_closing_times('data/closing-times.csv')

            house_race = Race.get(Race.race_id == '38529-OR')
            self.assertEqual(house_race.poll_closing_time, datetime(2014, 11, 4, 23, 0, 0))

            senate_race = Race.get(Race.race_id == '38145-OK')
            self.assertEqual(senate_race.poll_closing_time, datetime(2014, 11, 4, 20, 0, 0))

    def test_house_extra(self):
        with test_database(test_db, [Race,]):
            data.load_races('data/tests/init_races.json')
            data.load_house_extra('data/house-extra.csv', quiet=True)

            race = Race.get(Race.race_id == '38529-OR')
            self.assertEqual(race.previous_party, 'gop')
            self.assertFalse(race.featured_race)

    def test_senate_extra(self):
        with test_database(test_db, [Race,]):
            data.load_races('data/tests/init_races.json')
            data.load_senate_extra('data/senate-extra.csv', quiet=True)

            race = Race.get(Race.race_id == '38145-OK')
            self.assertEqual(race.previous_party, 'gop')

    def test_ballot_measures_extra(self):
        with test_database(test_db, [Race,]):
            data.load_races('data/tests/init_races.json')
            data.load_ballot_measures_extra('data/ballot-measures-extra.csv', quiet=True)

            race = Race.get(Race.race_id == '27456-MO')
            self.assertEqual(race.ballot_measure_description, 'Teacher Performance Evaluation (Amendment 3)')

