# /usr/bin/env python

from datetime import datetime

from fabric.api import task
from jinja2 import Template
import requests

import app_config
import models

LIMIT = 20 

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
            if post['type'] == 'video':
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
        slide = models.Slide.create(slug=slug, name=post_title, body=rendered_post)

        order = (models.SlideSequence.last() or 0) + 1

        sequence = models.SlideSequence.create(order=order, slide=slide)
        sequence.save()
        
        print '%s is slide number %s' % (slide.name, order)

def _render_post(post):
    post_date = datetime.fromtimestamp(post['timestamp'])
    if post_date.hour > 12: 
        formatted_hour = post_date.hour - 12
        period = 'p.m.'
    elif post_date.hour == 0:
        formatted_hour = 12
        period = 'a.m.'
    else: 
        formatted_hour = post_date.hour
        period = 'a.m.'
    post['formatted_date'] = '%s:%s %s EST' %(formatted_hour, post_date.minute, period)
    filename = '_tumblr_%s.html' % post['type']

    if post['type'] == 'photo':
        image = None
        for size in post['photos'][0]['alt_sizes']:
            if not image or size['width'] > image['width']:
                image = size
        post['image'] = image

    with open('templates/%s' % filename) as f:
        template = Template(f.read())

    return template.render(**post)

