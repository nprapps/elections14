#!/usr/bin/env python

import csv
import json

from fabric.api import task
import requests

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
                .split(u'fbcdn.net/')[1]\
                .replace('_8.jpg', '.jpg'))
        setattr(
            self,
            'local_img_url',
            'assets/instagram/nprparty-instagram-%s' % self.image_url\
                .split(u'fbcdn.net/')[1]\
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

    print "Writing %s photos to JSON." % len(payload)
    with open('www/live-data/photos.json', 'wb') as writefile:
        writefile.write(json.dumps(payload))

@task
def get_photos():
    get_photo_csv()
    parse_photo_csv()
