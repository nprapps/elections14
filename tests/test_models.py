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
            race = Race.get()

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
        pass

    def test_has_incumbent(self):
        pass

    def test_count_votes(self):
        with test_database(test_db, [Race, Candidate], create_tables=True):
            data.load_races('data/tests/init_races.json')
            data.load_candidates('data/tests/init_candidates.json')
            data.load_updates('data/tests/update.json')

            race = Race.select().get()
            self.assertTrue(race.is_reporting())
            self.assertEqual(race.count_votes(), 600000)

    def test_top_candidates(self):
        pass

class CandidateTestCase(unittest.TestCase):
    """
    Test Candidate model methods.
    """
    def test_is_winner(self):
        pass

    def test_vote_percent(self):
        pass
