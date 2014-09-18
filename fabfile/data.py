#!/usr/bin/env python

"""
Commands that update or process the application data.
"""
from datetime import datetime
import json
import os
import shutil

import boto.dynamodb
from boto.dynamodb.condition import GE
import copytext
from fabric.api import env, local, settings, task
from facebook import GraphAPI
from twitter import Twitter, OAuth

import app_config
import admin_app

def postgres_command(cmd ):
    local('export PGPASSWORD=$elections14_POSTGRES_PASSWORD && %s --username=$elections14_POSTGRES_USER --host=$elections14_POSTGRES_HOST --port=$elections14_POSTGRES_PORT' % cmd)

@task
def bootstrap():
    """
    Resets the local environment to a fresh copy of the db and data.
    """
    secrets = app_config.get_secrets()

    if env.settings:
        with settings(warn_only=True):
            postgres_command('dropdb %s' % app_config.PROJECT_SLUG)
            postgres_command('createdb %s' % app_config.PROJECT_SLUG)
    else:
        with settings(warn_only=True):
            local('dropdb %s' % app_config.PROJECT_SLUG)
            local('echo "CREATE USER %s WITH PASSWORD \'%s\';" | psql' % (app_config.PROJECT_SLUG, secrets['POSTGRES_PASSWORD']))

        local('createdb -O %s %s' % (app_config.PROJECT_SLUG, app_config.PROJECT_SLUG))

    import models

    models.Race.create_table()
    models.Candidate.create_table()
    models.Slide.create_table()
    models.SlideSequence.create_table()

    admin_app.auth.User.create_table()
    admin_user = admin_app.auth.User(username='admin', email='', admin=True, active=True)
    admin_user.set_password(secrets.get('ADMIN_PASSWORD'))
    admin_user.save()

    load_slide_fixtures()

    with open('data/races.json') as f:
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

    with open('data/candidates.json') as f:
        candidates = json.load(f)

        for candidate in candidates:
            models.Candidate.create(
                first_name = candidate['first_name'],
                last_name = candidate['last_name'],
                party = candidate['party'],
                race = models.Race.get(models.Race.race_id == candidate['race_id']),
                candidate_id = candidate['candidate_id'],
            )

@task(default=True)
def update(test=False):
    """
    Stub function for updating app-specific data.
    """
    import models

    #update_featured_social()

    if test:
        shutil.copyfile('data/fake_update.json', 'data/update.json')

    if not os.path.exists('data/update.json'):
        return
    
    update_flat = []

    with open('data/update.json') as f:
        races = json.load(f)

        for race in races:
            race_model = models.Race.get(models.Race.race_id == race['race_id'])

            race_model.is_test = race['is_test']
            race_model.precincts_reporting = race['precincts_reporting']
            race_model.precincts_total = race['precincts_total']
            race_model.last_updated = race['last_updated']

            race_model.save()

            for candidate in race['candidates']:
                # Select candidate by candidate_id AND race_id, since they can appear in multiple races
                candidate_model = models.Candidate.get(models.Candidate.candidate_id == candidate['candidate_id'], models.Candidate.race == race_model)

                candidate_model.vote_count = candidate['vote_count']
                candidate_model.ap_winner = candidate.get('ap_winner', False)

                candidate_model.save()

            update_flat.append(race_model.flatten(update_only=True))

    with open('www/live-data/update.json', 'w') as f:
        json.dump(update_flat, f, cls=models.ModelEncoder)

    print 'Updated %i races' % len(races)
    print 'Updated %i candidates' % sum([len(race['candidates']) for race in races])


@task
def get_quiz_answers():
    conn = boto.dynamodb.connect_to_region('us-west-2')

    table = conn.get_table('elections14-game')

    recent_answers = table.scan({ 'timestamp': GE('1410800598040') })

    print recent_answers.count

    for answer in recent_answers:
        print answer

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
def load_slide_fixtures():
    import models

    path = 'www/assets/slide-mockups/'
    files = [ f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f)) ]
    files.sort()
    for i, filename in enumerate(files):
        body = '<img src="%s/assets/slide-mockups/%s"/>' % (app_config.S3_BASE_URL, filename)
        name = 'Test slide: %s' % filename[0:-4]
        slide = models.Slide.create(body=body, name=name)
        slide.save()
        sequence = models.SlideSequence.create(sequence=i, slide=slide)
        sequence.save()
