import datetime
import os
import re
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
    # state_name = CharField(max_length=255)
    office_id = CharField(max_length=255)
    office_name = CharField(max_length=255)
    seat_name = CharField(null=True)
    seat_number = IntegerField(null=True)
    race_id = CharField(unique=True)
    race_type = CharField()
    last_updated = DateTimeField()

    # data from update
    precincts_total = IntegerField(null=True)
    precincts_reporting = IntegerField(null=True)
    office_description = CharField(null=True)
    uncontested = BooleanField(default=False)
    is_test = BooleanField(default=False)
    number_in_runoff = CharField(null=True)

    # NPR data
    featured_race = BooleanField(default=False)
    accept_ap_call = BooleanField(default=True)
    poll_closing_time = DateTimeField(null=True)
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

    def save(self, *args, **kwargs):
        """
        Slugify before saving!
        """
        if not self.slug:
            self.slugify()

        super(Race, self).save(*args, **kwargs)

    def slugify(self):
        """
        Generate a slug for this playground.
        """
        bits = []

        for field in ['state_postal', 'office_name', 'seat_name']:
            attr = getattr(self, field)

            if attr:
                attr = attr.lower()
                attr = re.sub(r"[^\w\s]", '', attr)
                attr = re.sub(r"\s+", '-', attr)
                bits.append(attr)

        base_slug = '-'.join(bits)
        slug = base_slug
        i = 1

        while Race.select().where(Race.slug == slug).count():
            i += 1
            slug = '%s-%i' % (base_slug, i)

        self.slug = slug

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
    party = CharField(max_length=255)
    race = ForeignKeyField(Race)
    candidate_id = CharField(unique=True)

    # update data
    incumbent = BooleanField(default=False)
    ballot_order = CharField(null=True)
    vote_count = IntegerField(default=False)

    # NPR data
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
