# /usr/bin/env python

from datetime import datetime
import json

from fabric.api import task
import requests

import app_config
import models

LIMIT = 20

UNSUPPORTED_TYPES = ['video', 'audio', 'link', 'chat', 'answer']

@task
def update():
    """
    Fetch latests posts from Tumblr API.
    """
    secrets = app_config.get_secrets()

    offset = 0
    total_posts = 1

    while offset < total_posts:
        print 'Fetching posts %i-%i' % (offset, offset + LIMIT)

        response = requests.get('http://api.tumblr.com/v2/blog/%s.tumblr.com/posts' % app_config.TUMBLR_NAME, params={
            'api_key':secrets['TUMBLR_CONSUMER_KEY'],
            'limit': LIMIT,
            'offset': offset
        })

        data = response.json()

        total_posts = data['response']['total_posts']
        posts = data['response']['posts']

        for post in posts:
            if post['type'] in UNSUPPORTED_TYPES:
                continue

            if datetime.fromtimestamp(post['timestamp']) < app_config.TUMBLR_NOT_BEFORE:
                print 'Skipping old post'
                continue

            _create_slide(post)

        offset += LIMIT

def _create_slide(post):
    slug = 'tumblr-%i' % post['id']
    post_title = post.get('title', None) or post['slug']
    view_name = 'tumblr_%s' % post['type']
    data = json.dumps(post)

    try:
        slide = models.Slide.get(slug=slug)
        print 'Updating post %s' % slug
        slide.name = post_title
        slide.data = data 
        slide.save()
    except models.Slide.DoesNotExist:
        print 'Creating post %s' % slug
        slide = models.Slide.create(slug=slug, name=post_title, data=data, view_name=view_name)

