import datetime
import os
import time

from flask import json
from peewee import Model, PostgresqlDatabase, BooleanField, DateField, DateTimeField, ForeignKeyField, IntegerField, TextField, CharField

import app_config

secrets = app_config.get_secrets()
db = PostgresqlDatabase(
    app_config.PROJECT_SLUG,
    user=app_config.PROJECT_SLUG,
    password=secrets.get('POSTGRES_PASSWORD', None),
    host=secrets.get('POSTGRES_HOST', 'localhost'),
    port=secrets.get('POSTGRES_PORT', 5432)
)

class PSQLMODEL(Model):
    """
    Base class for Peewee models. Ensures they all live in the same database.
    """
    def to_dict(self):
        return dict(self.__dict__['_data'])

    class Meta:
        database = db

class Race(PSQLMODEL):
    slug = CharField(max_length=255)
    state_postal = CharField(max_length=255)
    state_name = CharField(max_length=255)
    office_code = CharField(max_length=255)
    office_name = CharField(max_length=255)
    district_id = IntegerField()
    district_name = CharField(max_length=255, null=True)
    accept_ap_call = BooleanField(default=True)
    poll_closing_time = DateTimeField(null=True)
    # featured_race = BooleanField(default=False)
    # prediction = CharField(null=True)
    total_precincts = IntegerField(null=True)
    is_test = CharField(null=True)
    election_date = CharField(null=True)
    county_number = CharField(null=True)
    fips = CharField(null=True)
    county_name = CharField(null=True)
    race_number = CharField(null=True)
    race_type_id = CharField(null=True)
    seat_name = CharField(null=True)
    race_type_party = CharField(null=True)
    race_type = CharField(null=True)
    office_description = CharField(null=True)
    number_of_winners = CharField(null=True)
    number_in_runoff = CharField(null=True)

    # Status
    precincts_reporting = IntegerField(null=True)
    ap_called = BooleanField(default=False)
    ap_called_time = DateTimeField(null=True)
    npr_called = BooleanField(default=False)
    npr_called_time = DateTimeField(null=True)

    def __unicode__(self):
        return u'%s: %s-%s' % (
            self.office_name,
            self.state_postal,
            self.district_id
        )

    @property
    def winner(self):
        for candidate in Candidate.select().where(Candidate.race == self):
            if self.accept_ap_call == True:
                if candidate.ap_winner == True:
                    if candidate.party == 'GOP':
                        return 'r'
                    elif candidate.party == 'Dem':
                        return 'd'
                    else:
                        return 'o'
            else:
                if candidate.npr_winner == True:
                    if candidate.party == 'GOP':
                        return 'r'
                    elif candidate.party == 'Dem':
                        return 'd'
                    else:
                        return 'o'
        return None

    @property
    def called(self):
        if self.accept_ap_call == True:
            return self.ap_called

        else:
            return self.npr_called

        return False

    def has_incumbents(self):
        for candidate in Candidate.select().where(Candidate.race == self):
            if candidate.incumbent == True:
                return True

        return False

    def total_votes(self):
        count = 0
        for c in Candidate.select().where(Candidate.race == self):
            count += c.vote_count
        return count

    def percent_reporting(self):
        try:
            getcontext().prec = 2
            percent = Decimal(self.precincts_reporting) / Decimal(self.total_precincts)
            return round(float(percent) * 100, 0)
        except InvalidOperation:
            return 0.0


class Candidate(PSQLMODEL):
    """
    Normalizes the candidate data into a candidate model.
    """
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    incumbent = BooleanField(default=False)
    party = CharField(max_length=255)
    race = ForeignKeyField(Race, null=True)
    candidate_number = CharField()
    ballot_order = CharField()

    # Status
    vote_count = IntegerField(default=False)
    ap_winner = BooleanField(default=False)
    npr_winner = BooleanField(default=False)

    def __unicode__(self):
        return u'%s %s (%s)' % (self.first_name, self.last_name, self.party)

    def vote_percent(self):
        try:
            getcontext().prec = 2
            percent = Decimal(self.vote_count) / Decimal(self.race.total_votes())
            return round(float(percent) * 100, 0)
        except InvalidOperation:
            return 0.0
