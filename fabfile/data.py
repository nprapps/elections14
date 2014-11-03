#!/usr/bin/env python

"""
Commands that update or process the application data.
"""
from datetime import datetime, timedelta
from time import sleep
from itertools import count
import json
import random

import copytext
from fabric.api import env, local, execute, require, run, settings, task
from facebook import GraphAPI
from twitter import Twitter, OAuth
from app_utils import eastern_now

import app_config
import admin_app
import servers
import stack
import csv

SERVER_POSTGRES_CMD = 'export PGPASSWORD=$elections14_POSTGRES_PASSWORD && %s --username=$elections14_POSTGRES_USER --host=$elections14_POSTGRES_HOST --port=$elections14_POSTGRES_PORT'

@task(default=True)
def update():
    """
    Run all updates
    """
    load_updates('data/update.json')
    load_calls('data/calls.json')

@task
def query(q):
    """
    Execute a query on one of the servers.
    """
    require('settings', provided_by=['production', 'staging'])

    run(SERVER_POSTGRES_CMD % ('psql -q elections14 -c "%s"' % q))

@task
def server_reset_db():
    """
    Reset the database on a server.
    """
    with settings(warn_only=True):
        local(SERVER_POSTGRES_CMD % ('dropdb %s' % app_config.PROJECT_SLUG))
        local(SERVER_POSTGRES_CMD % ('createdb %s' % app_config.PROJECT_SLUG))

def local_reset_db():
    """
    Reset the database locally.
    """
    secrets = app_config.get_secrets()

    with settings(warn_only=True):
        local('dropdb %s' % app_config.PROJECT_SLUG)
        local('echo "CREATE USER %s WITH PASSWORD \'%s\';" | psql' % (app_config.PROJECT_SLUG, secrets['POSTGRES_PASSWORD']))

    local('createdb -O %s %s' % (app_config.PROJECT_SLUG, app_config.PROJECT_SLUG))

def create_tables():
    """
    Create the databse tables.
    """
    import models

    secrets = app_config.get_secrets()

    print 'Creating database tables'

    models.Race.create_table()
    models.Candidate.create_table()
    models.Slide.create_table()
    models.SlideSequence.create_table()

    print 'Setting up admin'

    admin_app.auth.User.create_table()
    admin_user = admin_app.auth.User(username='admin', email='', admin=True, active=True)
    admin_user.set_password(secrets.get('ADMIN_PASSWORD'))
    admin_user.save()


@task
def reset_server():
    require('settings', provided_by=['production', 'staging'])
    require('branch', provided_by=['master', 'stable'])

    with settings(warn_only=True):
        servers.stop_service('deploy_liveblog')
        servers.stop_service('deploy_results')
        servers.stop_service('uwsgi')
    servers.fabcast('ap.init ap.clear_calls data.bootstrap liveblog.update')
    servers.start_service('uwsgi')
    servers.start_service('deploy_liveblog')
    servers.start_service('deploy_results')

@task
def bootstrap():
    """
    Resets the local environment to a fresh copy of the db and data.
    """
    if env.settings:
        server_reset_db()
    else:
        local_reset_db()

    create_tables()

    load_races('data/init_races.json')
    load_candidates('data/init_candidates.json')
    load_closing_times('data/closing-times.csv')
    load_house_extra('data/house-extra.csv')
    load_senate_extra('data/senate-extra.csv')
    load_governor_extra('data/governor-extra.csv')
    load_ballot_measures_extra('data/ballot-measures-extra.csv')
    create_slides()
    stack.deploy()

def load_races(path):
    """
    Load AP race data from intermediary JSON into the database.
    """
    import models

    print 'Loading race data from AP init data on disk'

    with open(path) as f:
        races = json.load(f)

    now = eastern_now()

    with models.db.transaction():
        for race in races:
            models.Race.create(
                state_postal = race['state_postal'],
                office_id = race['office_id'],
                office_name = race['office_name'],
                seat_name = race['seat_name'],
                seat_number = race['seat_number'],
                race_id = race['race_id'],
                race_type = race['race_type'],
                last_updated = now,
            )

    print 'Loaded %i races' % len(races)

def load_candidates(path):
    """
    Load AP candidate data from intermediary JSON into the database.
    """
    import models

    print 'Loading candidate data from AP init data on disk'

    with open(path) as f:
        candidates = json.load(f)

    with models.db.transaction():
        for candidate in candidates:
            models.Candidate.create(
                first_name = candidate['first_name'],
                last_name = candidate['last_name'],
                party = candidate['party'],
                race = models.Race.get(models.Race.race_id == candidate['race_id']),
                candidate_id = candidate['candidate_id'],
                incumbent = candidate['incumbent'],
            )

    print 'Loaded %i candidates' % len(candidates)

@task()
def load_updates(path):
    """
    Update the latest results from the AP intermediary files.
    """
    import models

    races_updated = 0
    candidates_updated = 0

    now = eastern_now()

    print 'Loading latest results from AP update data on disk'

    with open(path) as f:
        races = json.load(f)

    for race in races:
        changed = False
        race_model = models.Race.get(models.Race.race_id == race['race_id'])

        for candidate in race['candidates']:
            # Select candidate by candidate_id AND race_id, since they can appear in multiple races
            candidate_model = models.Candidate.get(models.Candidate.candidate_id == candidate['candidate_id'], models.Candidate.race == race_model)

            if candidate.get('vote_count'):
                if candidate_model.vote_count != candidate['vote_count']:
                    changed = True
                    candidate_model.vote_count = candidate['vote_count']
                    candidate_model.save()
                    candidates_updated += 1

        if race_model.precincts_reporting != race['precincts_reporting']:
            changed = True

        if changed:
            race_model.last_updated = now
            race_model.precincts_reporting = race['precincts_reporting']
            race_model.precincts_total = race['precincts_total']
            race_model.save()
            races_updated += 1

    print 'Updated %i races' % races_updated
    print 'Updated %i candidates' % candidates_updated

@task
def load_calls(path):
    """
    Update the latest calls from the AP intermediary files.
    """
    import models

    races_updated = 0
    candidates_updated = 0
    num_winners = 0
    num_runoff_winners = 0

    print 'Loading latest calls from AP update data on disk'

    with open(path) as f:
        races = json.load(f)

    for race in races:
        race_model = models.Race.get(models.Race.race_id == race['race_id'])

        if race.get('ap_winner'):
            candidate_model = models.Candidate.get(models.Candidate.candidate_id == race['ap_winner'])
            candidate_model.ap_winner = True
            candidate_model.save()
            candidates_updated += 1
            num_winners += 1

        if race.get('ap_runoff_winners'):
            race_model.number_in_runoff = len(race['ap_runoff_winners'])

            for id in race['ap_runoff_winners']:
                candidate_model = models.Candidate.get(models.Candidate.candidate_id == id)
                candidate_model.ap_runoff_winner = True
                candidate_model.save()
                candidates_updated += 1
                num_runoff_winners += 1

        if race.get('ap_winner') or race.get('ap_runoff_winners'):
            race_model.ap_called = True
            race_model.ap_called_time = datetime.strptime(race['ap_called_time'], '%Y-%m-%dT%H:%M:%SZ')
            race_model.save()
            races_updated += 1

    print 'Updated %i races' % races_updated
    print 'Updated %i candidates' % candidates_updated
    print 'Found %i winners' % num_winners
    print 'Found %i runoff winners' % num_runoff_winners

@task
def update_featured_social():
    """
    Update featured tweets
    """
    COPY = copytext.Copy(app_config.COPY_PATH)
    secrets = app_config.get_secrets()

    # Twitter
    print 'Fetching tweets...'

    twitter_api = Twitter(
        auth=OAuth(
            secrets['TWITTER_API_OAUTH_TOKEN'],
            secrets['TWITTER_API_OAUTH_SECRET'],
            secrets['TWITTER_API_CONSUMER_KEY'],
            secrets['TWITTER_API_CONSUMER_SECRET']
        )
    )

    tweets = []

    for i in range(1, 4):
        tweet_url = COPY['share']['featured_tweet%i' % i]

        if isinstance(tweet_url, copytext.Error) or unicode(tweet_url).strip() == '':
            continue

        tweet_id = unicode(tweet_url).split('/')[-1]

        tweet = twitter_api.statuses.show(id=tweet_id)

        creation_date = datetime.strptime(tweet['created_at'],'%a %b %d %H:%M:%S +0000 %Y')
        creation_date = '%s %i' % (creation_date.strftime('%b'), creation_date.day)

        tweet_url = 'http://twitter.com/%s/status/%s' % (tweet['user']['screen_name'], tweet['id'])

        photo = None
        html = tweet['text']
        subs = {}

        for media in tweet['entities'].get('media', []):
            original = tweet['text'][media['indices'][0]:media['indices'][1]]
            replacement = '<a href="%s" target="_blank" onclick="_gaq.push([\'_trackEvent\', \'%s\', \'featured-tweet-action\', \'link\', 0, \'%s\']);">%s</a>' % (media['url'], app_config.PROJECT_SLUG, tweet_url, media['display_url'])

            subs[original] = replacement

            if media['type'] == 'photo' and not photo:
                photo = {
                    'url': media['media_url']
                }

        for url in tweet['entities'].get('urls', []):
            original = tweet['text'][url['indices'][0]:url['indices'][1]]
            replacement = '<a href="%s" target="_blank" onclick="_gaq.push([\'_trackEvent\', \'%s\', \'featured-tweet-action\', \'link\', 0, \'%s\']);">%s</a>' % (url['url'], app_config.PROJECT_SLUG, tweet_url, url['display_url'])

            subs[original] = replacement

        for hashtag in tweet['entities'].get('hashtags', []):
            original = tweet['text'][hashtag['indices'][0]:hashtag['indices'][1]]
            replacement = '<a href="https://twitter.com/hashtag/%s" target="_blank" onclick="_gaq.push([\'_trackEvent\', \'%s\', \'featured-tweet-action\', \'hashtag\', 0, \'%s\']);">%s</a>' % (hashtag['text'], app_config.PROJECT_SLUG, tweet_url, '#%s' % hashtag['text'])

            subs[original] = replacement

        for original, replacement in subs.items():
            html =  html.replace(original, replacement)

        # https://dev.twitter.com/docs/api/1.1/get/statuses/show/%3Aid
        tweets.append({
            'id': tweet['id'],
            'url': tweet_url,
            'html': html,
            'favorite_count': tweet['favorite_count'],
            'retweet_count': tweet['retweet_count'],
            'user': {
                'id': tweet['user']['id'],
                'name': tweet['user']['name'],
                'screen_name': tweet['user']['screen_name'],
                'profile_image_url': tweet['user']['profile_image_url'],
                'url': tweet['user']['url'],
            },
            'creation_date': creation_date,
            'photo': photo
        })

    # Facebook
    print 'Fetching Facebook posts...'

    fb_api = GraphAPI(secrets['FACEBOOK_API_APP_TOKEN'])

    facebook_posts = []

    for i in range(1, 4):
        fb_url = COPY['share']['featured_facebook%i' % i]

        if isinstance(fb_url, copytext.Error) or unicode(fb_url).strip() == '':
            continue

        fb_id = unicode(fb_url).split('/')[-1]

        post = fb_api.get_object(fb_id)
        user  = fb_api.get_object(post['from']['id'])
        user_picture = fb_api.get_object('%s/picture' % post['from']['id'])
        likes = fb_api.get_object('%s/likes' % fb_id, summary='true')
        comments = fb_api.get_object('%s/comments' % fb_id, summary='true')
        #shares = fb_api.get_object('%s/sharedposts' % fb_id)

        creation_date = datetime.strptime(post['created_time'],'%Y-%m-%dT%H:%M:%S+0000')
        creation_date = '%s %i' % (creation_date.strftime('%b'), creation_date.day)

        # https://developers.facebook.com/docs/graph-api/reference/v2.0/post
        facebook_posts.append({
            'id': post['id'],
            'message': post['message'],
            'link': {
                'url': post['link'],
                'name': post['name'],
                'caption': (post['caption'] if 'caption' in post else None),
                'description': post['description'],
                'picture': post['picture']
            },
            'from': {
                'name': user['name'],
                'link': user['link'],
                'picture': user_picture['url']
            },
            'likes': likes['summary']['total_count'],
            'comments': comments['summary']['total_count'],
            #'shares': shares['summary']['total_count'],
            'creation_date': creation_date
        })

    # Render to JSON
    output = {
        'tweets': tweets,
        'facebook_posts': facebook_posts
    }

    with open('data/featured.json', 'w') as f:
        json.dump(output, f)

@task
def load_closing_times(path):
    """
    Load poll closing times
    """
    import models

    print 'Loading poll closing times from disk'

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:

            closing = datetime.strptime(row['close_time'], '%m/%d/%Y %H:%M:%S')
            update = models.Race.update(poll_closing_time=closing).where(models.Race.state_postal == row['state'])
            update.execute()

@task
def load_house_extra(path, quiet=False):
    """
    Load extra data (featured status, last party in power) for
    house of reps
    """
    print 'Loading house extra data from disk'

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            _save_house_row(row, quiet)

def _save_house_row(row, quiet=False):
    """
    Merge house data with existing record
    """
    import models

    try:
        state_postal = row['district'][0:2]
        district = int(row['district'][2:])
        existing = models.Race.get(models.Race.office_name == 'U.S. House', models.Race.state_postal == state_postal, models.Race.seat_number == district)

        existing.previous_party = row['party']

        if row['featured'] == '1':
            existing.featured_race = True

        if row['obama_gop'] == '1':
            existing.obama_gop = True

        if row['romney_dem'] == '1':
            existing.romney_dem = True

        if row['bluedog'] == '1':
            existing.bluedog = True

        if row['rematch_result'] and row['rematch_description']:
            existing.rematch_result = row['rematch_result']
            existing.rematch_description = row['rematch_description']

        if row['freshmen'] == '1':
            existing.freshmen = True

        existing.save()

    except models.Race.DoesNotExist:
        if not quiet:
            print 'House race named %s does not exist in AP data' % row['district']


@task
def load_senate_extra(path, quiet=False):
    """
    Load extra data (last party in power) for
    senate
    """
    print 'Loading senate extra data from disk'

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            _save_senate_row(row, quiet)

def _save_senate_row(row, quiet):
    """
    Merge senate data with existing record
    """
    import models

    try:
        state_postal = row['state']
        seat_number = row['seat_number']
        if seat_number == '':
            seat_number = 0
        else:
            seat_number = int(seat_number)

        existing = models.Race.get(models.Race.office_name == 'U.S. Senate', models.Race.state_postal == state_postal, models.Race.seat_number == seat_number)
        existing.previous_party = row['party']

        if row['female_incumbent'] == '1':
            existing.female_incumbent = True

        if row['female_candidate'] == '1':
            existing.female_candidate = True

        if row['romney_dem'] == '1':
            existing.romney_dem = True

        existing.save()

    except models.Race.DoesNotExist:
        if not quiet:
            print 'Senate race named %s %s does not exist in AP data' % (row['state'], row['seat_number'])

@task
def load_governor_extra(path, quiet=False):
    """
    Load extra data (last party in power) for
    senate
    """
    print 'Loading governor extra data from disk'

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            _save_governor_row(row, quiet)

def _save_governor_row(row, quiet):
    """
    Merge senate data with existing record
    """
    import models

    try:
        state_postal = row['state']

        existing = models.Race.get(models.Race.office_name == 'Governor', models.Race.state_postal == state_postal)
        existing.previous_party = row['party']

        if row['female_incumbent'] == '1':
            existing.female_incumbent = True

        if row['female_candidate'] == '1':
            existing.female_candidate = True

        existing.save()

    except models.Race.DoesNotExist:
        if not quiet:
            print 'Governor race in %s does not exist in AP data' % (row['state'])

@task
def load_ballot_measures_extra(path, quiet=False):
    """
    Load extra ballot measure info
    """
    print 'Loading ballot measure extra data from disk'

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            _save_ballot_measure_row(row, quiet)

def _save_ballot_measure_row(row, quiet):
    """
    Save a ballot measure row
    """
    import models

    try:
        race = models.Race.get(race_id=row['race_id'])
        race.ballot_measure_description = row['description']
        race.featured_race = True
        race.save()
    except models.Race.DoesNotExist:
        if not quiet:
            print 'Ballot measure %s (%s) does not exist in AP data' % (row['race_id'], row['description'])

@task
def create_slides():
    """
    Load mockup slides from assets directory.
    """
    import models

    models.SlideSequence.delete().execute()
    models.Slide.delete().execute()

    it = count()
    _create_slide('State Senate Results', '_state_senate_slide', 20, it.next())
    _create_slide('State House Results', '_state_house_slide', 20, it.next())
    _create_slide('Senate Big Board', 'senate_big_board', 20, it.next())
    _create_slide('House Big Board One', 'house_big_board_one', 20, it.next())
    _create_slide('House Big Board Two', 'house_big_board_two', 20, it.next())
    _create_slide('Governor Big Board', 'governor_big_board', 20, it.next())
    _create_slide('Ballot Measures Big Board', 'ballot_measures_big_board', 20, it.next())
    _create_slide('Balance of Power Graphic', 'balance_of_power', 10, it.next())
    _create_slide('House Democrats in Romney-Won Districts', 'romney_dems', 10, it.next())
    _create_slide('Senate Democrats in Romney-Won States', 'romney_senate_dems', 10, it.next())
    _create_slide('Republicans in Obama-Won Districts', 'obama_reps', 10, it.next())
    _create_slide('Incumbent Losers', 'incumbents_lost', 10, it.next())
    _create_slide('House Freshmen Results', 'house_freshmen', 10, it.next())
    _create_slide('Recent Senate Calls', 'recent_senate_calls', 10, it.next())
    _create_slide('Recent Governor Calls', 'recent_governor_calls', 10, it.next())

def _create_slide(slug, view, time_on_screen, i):
    import models

    body = ''
    slide = models.Slide.create(body=body, name=slug, view_name=view, time_on_screen=time_on_screen)
    models.SlideSequence.create(order=i, slide=slide)

@task
def mock_results(folder='data'):
    """
    Fake out some election results
    """
    import models

    print "Generating fake data"

    for race in models.Race.select():
        race.accept_ap_call = False
        race.ap_called = False
        _fake_precincts_reporting(race)
        _fake_called_status(race)
        _fake_results(race)
        race.save()

def _fake_incumbent(race):
    """
    Fake one incumbent for a race
    """
    import models
    candidates = race.candidates.where((models.Candidate.party == "GOP") | (models.Candidate.party == "Dem"))
    try:
        candidate = candidates[random.randint(0,1)]
        candidate.incumbent = True
        candidate.save()
    except IndexError:
        pass

def _fake_previous_party(race):
    """
    Fake out previous party for each seat
    """
    import models
    incumbent_query = race.candidates.where(models.Candidate.incumbent == True)
    if incumbent_query.count() > 0:
        incumbent = incumbent_query[0]
        race.previous_party = incumbent.party.lower()
    else:
        race.previous_party = random.choice(['gop', 'dem', 'other'])

def _fake_precincts_reporting(race):
    """
    Fake precincts reporting
    """
    race.precincts_total = random.randint(2000, 4000)
    if random.choice([True, True, False]):
        race.precincts_reporting = random.randint(200, race.precincts_total)
    else:
        race.precincts_reporting = 0


def _fake_called_status(race):
    """
    Fake AP called status, requires race to have closing time
    """
    if race.precincts_reporting > 0:
        race.ap_called = random.choice([True, True, True, False])

        if race.ap_called and race.poll_closing_time:
            race.accept_ap_call = True
            race.ap_called_time = race.poll_closing_time + timedelta(hours=random.randint(1,3), minutes=random.randint(0,59))


def _fake_results(race):
    max_votes = 0
    max_candidate = None
    for candidate in race.candidates:
        candidate.ap_winner = False
        if (candidate.party in ['GOP', 'Dem'] or race.office_id == 'I') and race.precincts_reporting > 0:
            votes = random.randint(400000, 600000)
            candidate.vote_count = votes
            if votes > max_votes:
                max_candidate = candidate
                max_votes = votes
        else:
            candidate.vote_count = 0

        candidate.save()

    if max_candidate and race.precincts_reporting > 0 and race.ap_called and race.candidates.count > 1:
        max_candidate.ap_winner = True
        max_candidate.save()

@task
def play_fake_results(update_interval=60):
    """
    Play back faked results, poll closing time by poll closing time
    """
    import models
    from peewee import fn
    from app_utils import eastern_now

    print "Playing back results, ctrl-c to stop"

    ct_query = models.Race.select(fn.Distinct(models.Race.poll_closing_time)).order_by(models.Race.poll_closing_time)
    closing_times = [ct.poll_closing_time for ct in ct_query]
    closing_times = closing_times * 2
    closing_times.sort()

    try:
        for i, ct in enumerate(closing_times):
            races = models.Race.select().where(models.Race.poll_closing_time == ct)
            if i % 2 == 0:
                print "Polls close at %s, precincts reporting" % ct
                for race in races:
                    race.precincts_total = random.randint(2000, 4000)
                    race.precincts_reporting = random.randint(200, race.precincts_total - 200)
                    _fake_results(race)
                    race.last_updated = eastern_now()
                    race.save()
            else:
                print "Races are called!"
                for race in races:
                    race.ap_called = True
                    race.accept_ap_call = True
                    race.ap_called_time = datetime.now()
                    race.precincts_reporting = random.randint(race.precincts_total - 500, race.precincts_total)
                    _fake_results(race)
                    race.last_updated = eastern_now()
                    race.save()


            #if app_config.DEPLOYMENT_TARGET:
                #execute('liveblog.update')
                #execute('deploy_liveblog')
                #execute('deploy_bop')
                #execute('deploy_big_boards')
                #execute('deploy_results')

            sleep(float(update_interval))

        print "All done, resetting results"
        reset_results()
        play_fake_results()

    except KeyboardInterrupt:
        print "ctrl-c pressed, resetting results"
        reset_results()

@task
def clear_calls():
    """
    Reset calls in the DB
    """
    import models
    races = models.Race.select()
    for race in races:
        race.ap_called = False
        race.ap_called_time = None
        race.npr_called = False
        race.npr_called_time = None
        race.save()

@task
def reset_results():
    """
    Reset election results
    """
    import models

    races = models.Race.select()
    for race in races:
        race.precincts_reporting = 0
        race.ap_called_time = None
        race.ap_called = False
        race.accept_ap_call = False
        race.npr_called = False
        race.npr_called_time = None
        for candidate in race.candidates:
            candidate.total_votes = 0
            candidate.ap_winner = False
            candidate.npr_winner = False
            candidate.save()

        race.save()

"""
Dangerous commands
"""

@task
def tlaloc_god_of_thunder():
    """
    Kick all database connections
    """
    with settings(warn_only=True):
        query("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'elections14';")
