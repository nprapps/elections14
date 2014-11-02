#!/usr/bin/env python

import re

from peewee import fn, Model, PostgresqlDatabase, BooleanField, CharField, DateTimeField, ForeignKeyField, IntegerField, TextField
from decimal import Decimal

import app_config

secrets = app_config.get_secrets()

db = PostgresqlDatabase(
    app_config.DATABASE['name'],
    user=app_config.DATABASE['user'],
    password=app_config.DATABASE['password'],
    host=app_config.DATABASE['host'],
    port=app_config.DATABASE['port']
)

# Indepdendent candidate overrides, (AP race_id, candidate_id) two-tuple mapping
DEMOCRAT_OVERRIDES = {
    '17585-KS': '6081-KS',   # KS senate, Greg Orman (I)
    '20157-LA': '23579-LA',  # LA Senate, Mary Landrieu (D)
    '2010-AK':  '6399-AK',   # AK gov, Bill Walker (I)
}
REPUBLICAN_OVERRIDES = {
    '5707-CA':  '19804-CA',  # CA House District 17, Ro Khanna (D)
    '20157-LA': '23859-LA',  # LA Senate, Bill Cassidy (R)
}

USE_LEADING_CANDIDATES = {
    # SD Senate: Rounds, Weiland, Pressler
    '42003-SD': ['47394-SD', '47392-SD', '47534-SD'] 
}

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

class SlugModel(BaseModel):
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

class Race(SlugModel):
    """
    Race model.
    """
    slug_fields = ['state_postal', 'office_name', 'seat_name']

    # data from init
    race_id = CharField(primary_key=True)
    state_postal = CharField(max_length=255)
    office_id = CharField(max_length=255)
    office_name = CharField(max_length=255)
    seat_name = CharField(null=True)
    seat_number = IntegerField(null=True)
    race_type = CharField()
    last_updated = DateTimeField(null=True)

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
    ballot_measure_description = CharField(max_length=255, null=True)
    previous_party = CharField(max_length=5, null=True)
    obama_gop = BooleanField(default=False)
    romney_dem = BooleanField(default=False)
    bluedog = BooleanField(default=False)
    female_candidate = BooleanField(default=False)
    female_incumbent = BooleanField(default=False)
    rematch_result = TextField(null=True, default=None)
    rematch_description = TextField(null=True, default=None)
    freshmen = BooleanField(default=False)

    def __unicode__(self):
        return u'%s: %s-%s' % (
            self.office_name,
            self.state_postal,
            self.seat_name
        )

    def get_winning_party(self):
        """
        Return the winning party in this race, if any.
        """
        if self.is_called():
            for candidate in self.candidates.where(Candidate.race == self):
                if self.accept_ap_call:
                    if candidate.ap_winner:
                        if candidate.party == 'GOP':
                            return 'gop'
                        elif candidate.party == 'Dem':
                            return 'dem'
                        else:
                            return 'other'

                if candidate.npr_winner:
                    if candidate.party == 'GOP':
                        return 'gop'
                    elif candidate.party == 'Dem':
                        return 'dem'
                    else:
                        return 'other'

        return None

    def is_runoff(self):
        """
        Did the race lead to a runoff?
        """
        if self.accept_ap_call and self.number_in_runoff:
            return True
        else:
            return False

    def get_runoff_winners(self):
        """
        Get candidates who will appear in a runoff
        """
        if self.accept_ap_call and self.number_in_runoff:
            return self.candidates.where(Candidate.ap_runoff_winner == True)
        else:
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

    def party_changed(self):
        """
        Did the party change?
        """
        winner = self.get_winning_party()

        if winner:
            return winner != self.previous_party

        return None

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

    def has_incumbent(self):
        """
        Check if this Race has an incumbent candidate.
        """
        return bool(self.candidates.where(Candidate.incumbent == True).count())

    def count_votes(self):
        """
        Count the total votes cast for all candidates.
        """
        return self.candidates.select(fn.Sum(Candidate.vote_count)).scalar()

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

    def is_uncontested(self):
        """
        Return true if uncontested
        """
        if self.candidates.count() == 1:
            return True
        else:
            return False

    def top_candidates(self):
        """
        Return (dem, gop) pair of top candidates
        """

        if self.race_id in USE_LEADING_CANDIDATES.keys():
            candidates = USE_LEADING_CANDIDATES[self.race_id]
            return self._leading_top_candidates(candidates)
        else:
            return self._static_top_candidates()

    def _leading_top_candidates(self, candidates):
        """
        Get top candidates using total votes
        """
        candidates_query = self.candidates\
            .where(self.candidates.model_class.candidate_id << candidates)\
            .order_by(self.candidates.model_class.vote_count.desc())

        candidates = []
        for candidate in candidates_query:
            if candidate.get_party() == 'dem':
                dem = candidate
            if candidate.get_party() == 'gop':
                gop = candidate
            if candidate.get_party() == 'other':
                other = candidate

            candidates.append(candidate)

        if candidates[-1].get_party() == 'other':
            return (dem, gop)
        if candidates[-1].get_party() == 'gop':
            return (dem, other)
        if candidates[-1].get_party() == 'dem':
            return (other, gop)

    def _static_top_candidates(self):
        """
        Get top candidates using dem, gop pattern (with possibility for overrides)
        """
        try:
            if self.race_id in DEMOCRAT_OVERRIDES.keys():
                candidate_id = DEMOCRAT_OVERRIDES[self.race_id]
                dem = self.candidates.where(self.candidates.model_class.candidate_id == candidate_id).get()
            else:
                dem = self.candidates.where(self.candidates.model_class.party == "Dem").get()
        except Candidate.DoesNotExist:
            dem = None

        try:
            if self.race_id in REPUBLICAN_OVERRIDES.keys():
                candidate_id = REPUBLICAN_OVERRIDES[self.race_id]
                gop = self.candidates.where(self.candidates.model_class.candidate_id == candidate_id).get()
            else:
                gop = self.candidates.where(self.candidates.model_class.party == "GOP").get()
        except Candidate.DoesNotExist:
            gop = None

        return (dem, gop)

    def top_choices(self):
        """
        Return (yes, no) or (for, against) pair
        """
        yes = self.candidates.where((self.candidates.model_class.last_name == 'Yes') | (self.candidates.model_class.last_name == 'For')).get()
        no = self.candidates.where((self.candidates.model_class.last_name == 'No') | (self.candidates.model_class.last_name == 'Against')).get()
        return (yes, no)

class Candidate(SlugModel):
    """
    Candidate model.
    """
    slug_fields = ['first_name', 'last_name', 'candidate_id']

    # from init
    first_name = CharField(max_length=255, null=True,
        help_text='May be null for ballot initiatives')
    last_name = CharField(max_length=255)
    party = CharField(max_length=255, null=True)
    race = ForeignKeyField(Race, related_name='candidates')
    candidate_id = CharField(index=True)

    # update data
    incumbent = BooleanField(default=False, null=True)
    ballot_order = CharField(null=True)
    vote_count = IntegerField(default=False)
    ap_winner = BooleanField(default=False)
    ap_runoff_winner = BooleanField(default=False)

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

    def get_party(self):
        if self.party == 'Dem':
            return 'dem'

        elif self.party == 'GOP':
            return 'gop'

        else:
            return 'other'

    def is_winner(self):
        """
        Is the candidate the winner?
        """
        if self.race.is_called():
            if self.npr_winner:
                return True

            if self.race.accept_ap_call:
                if self.ap_winner:
                    return True

        return False

    def vote_percent(self):
        total_votes = self.race.count_votes()

        ratio = Decimal(self.vote_count) / Decimal(total_votes)

        return ratio * 100

class Slide(SlugModel):
    """
    Model for a slide in dynamic slide show
    """
    slug_fields = ['name']

    slug = CharField(max_length=255, primary_key=True)
    name = CharField(max_length=255)
    data = TextField(null=True)
    view_name = CharField(max_length=255)
    time_on_screen = IntegerField(default=15)

    def __unicode__(self):
        return self.name

class SlideSequence(BaseModel):
    """
    Defines a sequence of slides to play
    """
    order = IntegerField(primary_key=True)
    slide = ForeignKeyField(Slide)

    def __unicode__(self):
        return unicode(self.slide)

    @classmethod
    def first(cls):
        return cls.select(fn.Min(cls.order)).scalar() or 0

    @classmethod
    def last(cls):
        return cls.select(fn.Max(cls.order)).scalar() or 0

    @classmethod
    def stack(cls):
        sequences = cls.select().order_by(cls.order.asc())

        data = []

        for sequence in sequences:
            data.append({
                'slug': sequence.slide.slug,
                'time_on_screen': sequence.slide.time_on_screen
            })

        return data

