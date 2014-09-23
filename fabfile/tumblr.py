# /usr/bin/env python

from fabric.api import task
from jinja2 import Template
from peewee import fn
import requests

import app_config
import models

@task
def get_posts():
    """
    Fetch latests posts from Tumblr API.
    """
    secrets = app_config.get_secrets()

    response = requests.get('http://api.tumblr.com/v2/blog/%s.tumblr.com/posts' % app_config.TUMBLR_NAME, params={
        'api_key':secrets['TUMBLR_CONSUMER_KEY'],
    })
    posts = response.json()['response']['posts']

    for post in posts:
        if post['type'] == 'video':
            continue

        _create_slide(post)

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

        max = models.SlideSequence.select(fn.Max(models.SlideSequence.sequence)).scalar()
        if not max:
            max = 0
        sequence = models.SlideSequence.create(sequence=max+1, slide=slide)
        print '%s is slide number %s' % (slide.name, max)
        sequence.save()

def _render_post(post):
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

