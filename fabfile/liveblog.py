# /usr/bin/env python

from datetime import datetime

from dateutil.parser import parse
from fabric.api import task
from jinja2 import Template
import pytz
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
    rendered_post = _render_post(post)
    slug = 'tumblr-%i' % post['id']
    post_title = post['slug']

    try:
        slide = models.Slide.get(slug=slug)
        print 'Updating post %s' % slug
        slide.name = post_title
        slide.body = rendered_post
        slide.save()
    except models.Slide.DoesNotExist:
        print 'Creating post %s' % slug
        slide = models.Slide.create(slug=slug, name=post_title, body=rendered_post, view_name='_slide')

def _render_post(post):
    # Parse GMT date from API
    post_date = parse(post['date'])

    # Convert to Eastern time (EDT or EST)
    eastern = pytz.timezone('US/Eastern')

    # Format for display
    post['formatted_date'] = post_date.astimezone(eastern).strftime('%I:%M %p EST')

    filename = 'slides/tumblr_%s.html' % post['type']

    if post['type'] == 'photo':
        image = None
        for size in post['photos'][0]['alt_sizes']:
            if not image or size['width'] > image['width']:
                if size['width'] < 960:
                    image = size
        post['image'] = image

    with open('templates/%s' % filename) as f:
        template = Template(f.read())

    return template.render(**post)

