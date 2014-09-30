#!/usr/bin/env python

"""
Commands that update or process the application data.
"""
from datetime import datetime, timedelta
from itertools import count
import json
import random

import copytext
from dateutil.parser import parse
from fabric.api import env, local, require, run, settings, task
from facebook import GraphAPI
from twitter import Twitter, OAuth

import app_config
import admin_app
import servers
import csv

SERVER_POSTGRES_CMD = 'export PGPASSWORD=$elections14_POSTGRES_PASSWORD && %s --username=$elections14_POSTGRES_USER --host=$elections14_POSTGRES_HOST --port=$elections14_POSTGRES_PORT'

@task(default=True)
def update():
    """
    Run all updates
    """
    #update_featured_social()
    update_results()

@task
def query(q):
    """
    Execute a query on one of the servers.
    """
    require('settings', provided_by=['production', 'staging'])

    run(SERVER_POSTGRES_CMD % ('psql -q elections14 -c "%s"' % q))

def server_reset_db():
    """
    Reset the database on a server.
    """
    with settings(warn_only=True):
        services = ['uwsgi', 'stack', 'liveblog', 'instagram']
        for service in services:
            service_name = servers._get_installed_service_name(service)
            local('sudo service %s stop' % service_name)

        local(SERVER_POSTGRES_CMD % ('dropdb %s' % app_config.PROJECT_SLUG))
        local(SERVER_POSTGRES_CMD % ('createdb %s' % app_config.PROJECT_SLUG))

        for service in services:
            service_name = servers._get_installed_service_name(service)
            local('sudo service %s start' % service_name)

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
def bootstrap():
    """
    Resets the local environment to a fresh copy of the db and data.
    """
    if env.settings:
        server_reset_db()
    else:
        local_reset_db()

    create_tables()

    load_races('data/races.json')
    load_candidates('data/candidates.json')

def load_races(path):
    """
    Load AP race data from intermediary JSON into the database.
    """
    import models

    print 'Loading race data from AP init data on disk'

    with open(path) as f:
        races = json.load(f)

    for race in races:
        models.Race.create(
            state_postal = race['state_postal'],
            office_id = race['office_id'],
            office_name = race['office_name'],
            seat_name = race['seat_name'],
            seat_number = race['seat_number'],
            race_id = race['race_id'],
            race_type = race['race_type'],
            last_updated = race['last_updated'],
        )

def load_candidates(path):
    """
    Load AP candidate data from intermediary JSON into the database.
    """
    import models

    print 'Loading candidate data from AP init data on disk'

    with open(path) as f:
        candidates = json.load(f)

    for candidate in candidates:
        models.Candidate.create(
            first_name = candidate['first_name'],
            last_name = candidate['last_name'],
            party = candidate['party'],
            race = models.Race.get(models.Race.race_id == candidate['race_id']),
            candidate_id = candidate['candidate_id'],
        )

@task()
def update_results():
    """
    Update the latest results from the AP intermediary files.
    """
    import models

    races_updated = 0
    candidates_updated = 0

    print 'Loading latest results from AP update data on disk'

    with open('data/update.json') as f:
        races = json.load(f)

    for race in races:
        race_model = models.Race.get(models.Race.race_id == race['race_id'])

        # If race has not been updated, skip
        last_updated = parse(race['last_updated']).replace(tzinfo=None)

        if race_model.last_updated == last_updated:
            continue

        race_model.is_test = race['is_test']
        race_model.precincts_reporting = race['precincts_reporting']
        race_model.precincts_total = race['precincts_total']
        race_model.last_updated = last_updated

        race_model.save()

        races_updated += 1

        for candidate in race['candidates']:
            # Select candidate by candidate_id AND race_id, since they can appear in multiple races
            candidate_model = models.Candidate.get(models.Candidate.candidate_id == candidate['candidate_id'], models.Candidate.race == race_model)

            candidate_model.vote_count = candidate['vote_count']
            candidate_model.ap_winner = candidate.get('ap_winner', False)

            candidate_model.save()

            candidates_updated += 1

    print 'Updated %i races' % races_updated
    print 'Updated %i candidates' % candidates_updated

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
def load_house_extra():
    """
    Load extra data (featured status, poll close, last party in power) for
    house of reps
    """
    with open('data/house-extra.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('featured') == '1':
                _save_house_row(row)

def _save_house_row(row):
    """
    Merge house data with existing record
    """
    import models

    try:
        state_postal = row['district'][0:2]
        district = int(row['district'][2:])
        existing = models.Race.get(models.Race.office_name == 'U.S. House', models.Race.state_postal == state_postal, models.Race.seat_number == district)

        print "Updating %s" % existing
        existing.featured_race = True
        existing.previous_party = row['party']

        if row['poll_close'] != '':
            hours, minutes = row['poll_close'].split(':')
            existing.poll_closing_time = datetime(2014, 11, 4, int(hours), int(minutes))

        existing.save()

    except models.Race.DoesNotExist:
        print 'Race named %s does not exist in AP data' % row['district']


@task
def load_senate_extra():
    """
    Load extra data (featured status, poll close, last party in power) for
    senate
    """
    with open('data/senate-extra.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            _save_senate_row(row)

def _save_senate_row(row):
    """
    Merge senate data with existing record
    """
    import models

    try:
        state_postal = row['state']
        seat_number = row['seat_number']
        if seat_number == '':
            seat_number = None
        else:
            seat_number = int(seat_number)

        existing = models.Race.get(models.Race.office_name == 'U.S. Senate', models.Race.state_postal == state_postal, models.Race.seat_number == seat_number)

        print "Updating %s" % existing
        existing.featured_race = True
        existing.previous_party = row['party']

        if row['poll_close'] != '':
            hours, minutes = row['poll_close'].split(':')
            existing.poll_closing_time = datetime(2014, 11, 4, int(hours), int(minutes))

        existing.save()

    except models.Race.DoesNotExist:
        print 'Race named %s %s does not exist in AP data' % (row['state'], row['seat_number'])

@task
def mock_slides():
    """
    Load mockup slides from assets directory.
    """
    import models

    models.SlideSequence.delete().execute()
    models.Slide.delete().execute()

    it = count()
    _mock_slide_from_image('welcome.png', it.next())
    _mock_slide_with_pym('senate', 'results/senate/', it.next())
    _mock_slide_from_image('gif1.gif', it.next())

def _mock_slide_from_image(filename, i):
    import models

    body = '<img src="%s/assets/slide-mockups/%s"/>' % (app_config.S3_BASE_URL, filename)
    slide = models.Slide.create(body=body, name=filename)
    models.SlideSequence.create(order=i, slide=slide)

def _mock_slide_with_pym(slug, path, i):
    from flask import render_template
    import models
    import app

    context = {
        'slug': slug,
        'path': path
    }

    with app.app.test_request_context(path='/slides/pym'):
        body = render_template('slides/pym.html', **context)

    slide = models.Slide.create(slug=slug, body=body, name=slug)
    models.SlideSequence.create(order=i, slide=slide)

@task
def mock_results():
    """
    Fake out some election results
    """
    import models

    print "Generating fake data"

    for candidate in models.Candidate.select():
        candidate.incumbent = False
        candidate.save()

    for race in models.Race.select():
        race.accept_ap_call = False
        race.ap_called = False
        _fake_incumbent(race)
        _fake_previous_party(race)
        _fake_poll_closing_time(race)
        _fake_precincts_reporting(race)
        _fake_called_status(race)
        _fake_results(race)
        race.save()

    print "Loading real data where it exists"
    load_house_extra()
    load_senate_extra()

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

def _fake_poll_closing_time(race):
    """
    Fake poll closing time
    """
    first_close = datetime(2014, 11, 4, 7)
    closing_times = [first_close + timedelta(hours=delta) for delta in range(6)]
    race.poll_closing_time = random.choice(closing_times)


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
        if race.ap_called:
            race.accept_ap_call = True
            race.ap_called_time = race.poll_closing_time + timedelta(hours=random.randint(1,3), minutes=random.randint(0,59))


def _fake_results(race):
    max_votes = 0
    for candidate in race.candidates:
        candidate.ap_winner = False
        if candidate.party in ['GOP', 'Dem', 'Grn'] and race.precincts_reporting > 0:
            votes = random.randint(400000, 600000)
            candidate.vote_count = votes
            if votes > max_votes:
                max_candidate = candidate
                max_votes = votes
        else:
            candidate.vote_count = 0

        candidate.save()

    if race.precincts_reporting > 0 and race.ap_called and race.candidates.count > 1:
        max_candidate.ap_winner = True
        max_candidate.save()

