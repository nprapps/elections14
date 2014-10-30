#!/usr/bin/env python

import boto
from boto.s3.key import Key
from fabric.api import task

import app_config
import app

@task
def deploy():
    from flask import url_for

    with app.app.test_request_context():
        path = url_for('_stack_json')

    with app.app.test_request_context(path=path):
        view = app.__dict__['_stack_json']
        content = view()

    with open('www/live-data/stack.json', 'w') as f:
        f.write(content.data)

    if app_config.DEPLOYMENT_TARGET:
        for bucket in app_config.S3_BUCKETS:
            c = boto.connect_s3()
            b = c.get_bucket(bucket['bucket_name'])
            k = Key(b)
            k.key = 'live-data/stack.json'
            k.set_contents_from_filename('www/live-data/stack.json', headers={
                'cache-control': 'max-age=%i no-cache no-store must-revalidate' % app_config.MAX_AGE_CACHE_CONTROL_HEADER
            })
            k.make_public()
