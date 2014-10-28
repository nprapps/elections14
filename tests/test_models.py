#!/usr/bin/env python

from datetime import datetime
from decimal import Decimal
import unittest

from peewee import *
from playhouse.test_utils import test_database

from fabfile import data
from models import Race, Candidate

test_db = PostgresqlDatabase('elections14test')

class RaceTestCase(unittest.TestCase):
    """
    Test Race model methods.
    """
    def test_get_winning_party(self):
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')
            data.load_candidates('data/tests/init_candidates.json')
            race = Race.get(Race.race_id == '38529-OR')


            self.assertIsNone(race.get_winning_party())

            race.ap_called = True
            race.accept_ap_call = True
            race.save()

            winner = race.candidates.select()[0]
            winner.party = 'GOP'
            winner.ap_winner = True
            winner.save()

            self.assertEqual(race.get_winning_party(), 'gop')

            winner = race.candidates.select()[0]
            winner.party = 'Dem'
            winner.ap_winner = True
            winner.save()

            self.assertEqual(race.get_winning_party(), 'dem')

            winner = race.candidates.select()[0]
            winner.party = 'Lib'
            winner.ap_winner = True
            winner.save()

            self.assertEqual(race.get_winning_party(), 'other')

            race.accept_ap_call = False
            race.save()

            self.assertIsNone(race.get_winning_party())

            race.npr_called = True
            race.save()

            npr_winner = race.candidates.select()[1]
            npr_winner.party = 'GOP'
            npr_winner.npr_winner = True
            npr_winner.save()

            self.assertEqual(race.get_winning_party(), 'gop')

    def test_is_called(self):
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')

            race = Race.get()

            self.assertFalse(race.is_called())

            race.ap_called = True
            race.save()

            self.assertTrue(race.is_called())

            race.accept_ap_call = False
            race.save()

            self.assertFalse(race.is_called())

            race.npr_called = True
            race.save()
            
            self.assertTrue(race.is_called())

    def test_is_reporting(self):
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')
            race = Race.get()

            self.assertFalse(race.is_reporting())

            race.precincts_reporting = 100
            race.save()

            self.assertTrue(race.is_reporting())

    def test_party_changed(self):
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')
            data.load_candidates('data/tests/init_candidates.json')
            race = Race.get()

            self.assertIsNone(race.party_changed())

            race.ap_called = True
            race.previous_party = 'gop'
            race.save()

            winner = race.candidates.select()[0]
            winner.party = 'Dem'
            winner.ap_winner = True
            winner.save()

            self.assertEqual(race.get_winning_party(), 'dem')
            self.assertTrue(race.party_changed())

            race.previous_party = 'dem'
            race.save()

            self.assertFalse(race.party_changed())

    def test_get_called_time(self):
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')

            race = Race.get()

            self.assertIsNone(race.get_called_time())

            race.ap_called_time = datetime(2014, 1, 1)
            race.save()

            self.assertEqual(race.get_called_time(), datetime(2014, 1, 1))

            race.accept_ap_call = False
            race.save()

            self.assertIsNone(race.get_called_time())

            race.npr_called_time = datetime(2014, 2, 2)
            race.save()

            self.assertEqual(race.get_called_time(), datetime(2014, 2, 2))

    def test_precincts_reporting_percent(self):
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')
            data.load_candidates('data/tests/init_candidates.json')
            data.load_updates('data/tests/update.json')

            race = Race.select().get()
            race.precincts_reporting = 700
            race.precincts_total = 1100
            race.save()

            self.assertAlmostEqual(race.precincts_reporting_percent(), Decimal('63.636'), 3)

    def test_has_incumbent(self):
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')
            data.load_candidates('data/tests/init_candidates.json')

            race = Race.get(Race.race_id == '38529-OR')

            self.assertFalse(race.has_incumbent())

            incumbent = race.candidates.get()
            incumbent.incumbent = True
            incumbent.save()

            self.assertTrue(race.has_incumbent())

    def test_count_votes(self):
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')
            data.load_candidates('data/tests/init_candidates.json')
            data.load_updates('data/tests/update.json')

            race = Race.get(Race.race_id == '38529-OR')
            self.assertTrue(race.is_reporting())
            self.assertEqual(race.count_votes(), 600000)

    def test_top_candidates(self):
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')
            data.load_candidates('data/tests/init_candidates.json')
            data.load_updates('data/tests/update.json')

            race = Race.get(Race.race_id == '38529-OR')
            top_candidates = race.top_candidates()
            self.assertEqual(top_candidates[0].party, 'Dem')
            self.assertEqual(top_candidates[1].party, 'GOP')

    def test_top_choices(self):
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')
            data.load_candidates('data/tests/init_candidates.json')
            data.load_updates('data/tests/update.json')

            race = Race.get(Race.race_id == '27456-MO')
            top_choices = race.top_choices()
            self.assertEqual(top_choices[0].last_name, 'Yes')
            self.assertEqual(top_choices[1].last_name, 'No')


class CandidateTestCase(unittest.TestCase):
    """
    Test Candidate model methods.
    """
    def test_is_winner(self):
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')
            data.load_candidates('data/tests/init_candidates.json')

            race = Race.get(Race.race_id == '38529-OR')

            candidate = race.candidates.get() 
            candidate.ap_winner = True
            candidate.save()

            self.assertFalse(race.is_called())
            self.assertFalse(candidate.is_winner())

            race.ap_called = True
            race.npr_called = False
            race.accept_ap_call = True
            race.save()

            # Hack so the race updates override the cached FK
            candidate.race = race

            self.assertTrue(race.is_called())
            self.assertTrue(candidate.is_winner())

            candidate.ap_winner = False
            candidate.save()

            self.assertTrue(race.is_called())
            self.assertFalse(candidate.is_winner())

            race.accept_ap_call = False
            race.save()

            self.assertFalse(race.is_called())

            race.npr_called = True
            race.save()

            self.assertTrue(race.is_called())
            self.assertFalse(candidate.is_winner())

            candidate.npr_winner = True

            self.assertTrue(candidate.is_winner())

    def test_vote_percent(self):
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')
            data.load_candidates('data/tests/init_candidates.json')
            data.load_updates('data/tests/update.json')

            candidate_4848 = Candidate.get(Candidate.candidate_id == '4848')
            candidate_4642 = Candidate.get(Candidate.candidate_id == '4642')
            candidate_4979 = Candidate.get(Candidate.candidate_id == '4979')

            self.assertEqual(candidate_4848.vote_percent(), Decimal('25.0')) 
            self.assertAlmostEqual(candidate_4642.vote_percent(), Decimal('33.333'), 3) 
            self.assertAlmostEqual(candidate_4979.vote_percent(), Decimal('41.667'), 3) 

