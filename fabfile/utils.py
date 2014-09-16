#!/usr/bin/env python

"""
Utilities used by multiple commands.
"""
from fabric.api import local, prompt

import app_config

def confirm(message):
    """
    Verify a users intentions.
    """
    answer = prompt(message, default="Not at all")

    if answer.lower() not in ('y', 'yes', 'buzz off', 'screw you'):
        exit()

def deploy_json(src, dst):
    """
    Deploy the gzipped stuff to S3.
    """
    sync_gzip = 'aws s3 cp %s %s --acl "public-read" --content-encoding "gzip" --cache-control "max-age=5" --region "%s"'

    for bucket in app_config.S3_BUCKETS:
        local(sync_gzip % (src, 's3://%s/%s/%s' % (bucket['bucket_name'], app_config.PROJECT_SLUG, dst), bucket['region']))

