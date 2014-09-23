#!/usr/bin/env python

from datetime import datetime
import json
import re

from peewee import Model, PostgresqlDatabase, BooleanField, CharField, DateTimeField, ForeignKeyField, IntegerField, TextField
from decimal import Decimal

import app_config

secrets = app_config.get_secrets()

db = PostgresqlDatabase(
    app_config.PROJECT_SLUG,
    user=secrets.get('POSTGRES_USER', None),
    password=secrets.get('POSTGRES_PASSWORD', None),
    host=secrets.get('POSTGRES_HOST', 'localhost'),
    port=secrets.get('POSTGRES_PORT', 5432)
)

class ModelEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            encoded_object = obj.isoformat() 
        else:
            encoded_object = json.JSONEncoder.default(self, obj)

        return encoded_object

def slugify(bits):
    """
    Generate a slug.
    """
    slug_bits = []

    for bit in bits:
        if bit:
            bit = bit.lower()
            bit = re.sub(r"[^\w\s]", '', bit)
            bit = re.sub(r"\s+", '-', bit)
            slug_bits.append(bit)

    return '-'.join(slug_bits)

class BaseModel(Model):
    """
    Base class for Peewee models. Ensures they all live in the same database.
    """
    class Meta:
        database = db

    def save(self, *args, **kwargs):
        """
        Slugify before saving!
        """
        if not self.slug:
            self._slugify()

        super(BaseModel, self).save(*args, **kwargs)

    def _slugify(self):
        """
        Generate a slug for this model.
        """
        bits = []

        for field in self.slug_fields:
            bits.append(getattr(self, field))

        base_slug = slugify(bits)
        slug = base_slug
        i = 1

        model_class = self.__class__

        while model_class.select().where(model_class.slug == slug).count():
            i += 1
            slug = '%s-%i' % (base_slug, i)

        self.slug = slug

class Race(BaseModel):
    """
    Race model.
    """
    slug_fields = ['state_postal', 'office_name', 'seat_name']

    # data from init
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
    slug = CharField(max_length=255)
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
            self.seat_name
        )

    def get_winner(self):
        """
        Return the winner of this race, if any. 
        """
        for candidate in Candidate.select().where(Candidate.race == self):
            if self.accept_ap_call:
                if candidate.ap_winner:
                    if candidate.party == 'GOP':
                        return 'r'
                    elif candidate.party == 'Dem':
                        return 'd'
                    else:
                        return 'o'
            else:
                if candidate.npr_winner:
                    if candidate.party == 'GOP':
                        return 'r'
                    elif candidate.party == 'Dem':
                        return 'd'
                    else:
                        return 'o'

        return None

    def is_called(self):
        """
        Has this race been called?
        """
        if self.accept_ap_call:
            return self.ap_called
        else:
            return self.npr_called

        return False

    def is_reporting(self):
        """
        Are precincts reporting?
        """
        return bool(self.precincts_reporting)

    def get_called_time(self):
        """
        Get when this race was called.
        """
        if self.accept_ap_call:
            return self.ap_called_time
        else:
            return self.npr_called_time

    def precincts_reporting_percent(self):
        """
        Get precent precincts reporting
        """
        ratio = Decimal(self.precincts_reporting) / Decimal(self.precincts_total)
        return ratio * 100

    def has_incumbents(self):
        """
        Check if this Race has an incumbent candidate.
        """
        for candidate in Candidate.select().where(Candidate.race == self):
            if candidate.incumbent:
                return True

        return False

    def count_votes(self):
        """
        Count the total votes cast for all candidates.
        """
        count = 0

        for c in Candidate.select().where(Candidate.race == self):
            count += c.vote_count

        return count

    def flatten(self, update_only=False):
        UPDATE_FIELDS = [
            'id',
            'precincts_total',
            'precincts_reporting',
            'number_in_runoff'
        ]

        INIT_FIELDS = [
            'slug',
            'state_postal',
            'office_name',
            'seat_name',
            'seat_number', 
            'race_type' ,
            'last_updated',
            'office_description',
            'uncontested',
            'featured_race',
            'poll_closing_time',
        ]

        flat = {
            'candidates': []
        }

        for field in UPDATE_FIELDS:
            flat[field] = getattr(self, field)

        flat['called'] = self.is_called()
        flat['called_time'] = self.get_called_time()

        if not update_only:
            for field in INIT_FIELDS:
                flat[field] = getattr(self, field)

        for candidate in self.candidates:
            data = candidate.flatten(update_only=update_only)

            if self.accept_ap_call and candidate.ap_winner:
                data['winner'] = True
            elif candidate.npr_winner:
                data['winner'] = True
            else:
                data['winner'] = False

            flat['candidates'].append(data)

        return flat

    def top_candidates(self):
        try:
            dem = self.candidates.where(self.candidates.model_class.party == "Dem")[0]
        except IndexError:
            dem = None
        try:
            gop = self.candidates.where(self.candidates.model_class.party == "GOP")[0]
        except IndexError:
            gop = None

        return (dem, gop)

class Candidate(BaseModel):
    """
    Candidate model.
    """
    slug_fields = ['first_name', 'last_name', 'candidate_id']

    # from init
    first_name = CharField(max_length=255, null=True,
        help_text='May be null for ballot initiatives')
    last_name = CharField(max_length=255)
    party = CharField(max_length=255)
    race = ForeignKeyField(Race, related_name='candidates')
    candidate_id = CharField(index=True)

    # update data
    incumbent = BooleanField(default=False)
    ballot_order = CharField(null=True)
    vote_count = IntegerField(default=False)
    ap_winner = BooleanField(default=False)

    # NPR data
    slug = CharField(max_length=255) 
    npr_winner = BooleanField(default=False)

    def __unicode__(self):
        return u'%s %s (%s)' % (self.first_name, self.last_name, self.party)
    
    def flatten(self, update_only=False):
        UPDATE_FIELDS = [
            'id',
            'vote_count'
        ]

        INIT_FIELDS = [
            'slug',
            'first_name',
            'last_name',
            'party',
            'incumbent',
            'ballot_order'
        ]

        flat = {}

        for field in UPDATE_FIELDS:
            flat[field] = getattr(self, field)

        if not update_only:
            for field in INIT_FIELDS:
                flat[field] = getattr(self, field)

        return flat

    def is_winner(self):
        """
        Is the candidate the winner?
        """
        if self.race.is_called():
            if self.npr_winner:
                return True
            elif self.ap_winner:
                return True

        return False

    def vote_percent(self):
        total_votes = 0
        for candidate in self.race.candidates:
            total_votes += candidate.vote_count
        ratio = Decimal(self.vote_count) / Decimal(total_votes)
        return ratio * 100

class Slide(BaseModel):
    """
    Model for a slide in dynamic slide show
    """
    slug_fields = ['name']

    slug = CharField(max_length=255, primary_key=True)
    name = CharField(max_length=255)
    body = TextField()

    def __unicode__(self):
        return self.name

class SlideSequence(Model):
    """
    Defines a sequence of slides to play
    """

    class Meta:
        database = db

    sequence = IntegerField()
    slide = ForeignKeyField(Slide)

    def __unicode__(self):
        return self.slide.__unicode__()
