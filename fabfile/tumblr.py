# /usr/bin/env python

from pprint import pprint as pp

from fabric.api import local, task
from jinja2 import Template
from peewee import fn
import pytumblr

import app
import app_config
import models

@task
def get_posts():
    secrets = app_config.get_secrets()
    client = pytumblr.TumblrRestClient(
        secrets.get('TUMBLR_CONSUMER_KEY'),
        secrets.get('TUMBLR_CONSUMER_SECRET'),
        secrets.get('TUMBLR_TOKEN'),
        secrets.get('TUMBLR_TOKEN_SECRET')
    )

    resp = client.posts('stage-nprelections')

    posts = resp['posts']

    for post in posts:
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
        sequence = models.SlideSequence.create(sequence=max+1, slide=slide)
        print '%s is slide number %s' % (slide.name, max)
        sequence.save()

def _render_post(post):
    filename = '_tumblr_%s.html' % post['type']

    with open('templates/%s' % filename) as f:
        template = Template(f.read())
    return template.render(**post)

