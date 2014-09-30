#!/usr/bin/env python

import csv
import json

from fabric.api import task
from jinja2 import Template
import requests

import models

FIELDNAMES = ['date', 'username', 'caption', 'instagram_url', 'image', 'image_url', 'embed_code', 'approved']

class Photo(object):

    def __init__(self, **kwargs):
        for field in FIELDNAMES:
            if kwargs[field]:
                setattr(self, field, kwargs[field])
        setattr(
            self,
            'local_img_id',
            self.image_url\
                .split(u'/')[-1]\
                .replace('_n.jpg', '.jpg'))
        setattr(
            self,
            'local_img_url',
            'assets/instagram/nprparty-instagram-%s' % self.image_url\
                .split(u'/')[-1]\
                .replace('_n.jpg', '.jpg'))

def get_photo_csv():
    r = requests.get('https://docs.google.com/spreadsheets/d/1DAirjcVoeeLtfpurOzJIqqgLqOWClxCOCD_wIkMUscI/export?format=csv')
    with open('data/photos.csv', 'wb') as writefile:
        writefile.write(r.content)

def parse_photo_csv():
    with open('data/photos.csv', 'rb') as readfile:
        photos = list(csv.DictReader(readfile, fieldnames=FIELDNAMES))

    print "Processing %s entries from Google Docs." % len(photos)

    payload = []

    for photo in photos:
        if photo['approved'] != '':
            r = requests.get(photo['image_url'])
            if r.status_code == 200:
                p = Photo(**photo)
                payload.append(p.__dict__)
                with open('www/assets/instagram/nprparty-instagram-%s' % p.local_img_id, 'wb') as writefile:
                    writefile.write(r.content)

    _create_photo_grid(payload)

def _create_photo_grid(photos):
    rendered_grid = _render_photo_grid(photos)
    slug = 'instagram-grid'
    slide_title = 'Instagram Grid'

    try:
        slide = models.Slide.get(slug=slug)
        print 'Updating grid'
        slide.name = slide_title
        slide.body = rendered_grid
        slide.save()
    except models.Slide.DoesNotExist:
        print 'Creating grid'
        slide = models.Slide.create(slug=slug, name=slide_title, body=rendered_grid)

        order = (models.SlideSequence.last() or 0) + 1

        sequence = models.SlideSequence.create(order=order, slide=slide)
        sequence.save()
        
        print '%s is slide number %s' % (slide.name, order)


def _render_photo_grid(photos):
    filename = 'slides/instagram.html'

    payload = {
        "photos": photos
    }

    with open('templates/%s' % filename) as f:
        template = Template(f.read())

    return template.render(**payload)

@task
def get_photos():
    get_photo_csv()
    parse_photo_csv()

