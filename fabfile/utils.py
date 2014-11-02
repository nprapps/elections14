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

def _gzip(in_path='www', out_path='.gzip'):
    """
    Gzips everything in www and puts it all in gzip
    """
    local('python gzip_assets.py %s %s' % (in_path, out_path))

def _deploy_to_s3(path='.gzip', sync_assets=True):
    """
    Deploy the gzipped stuff to S3.
    """
    print "Uploading %s to S3" % path

    # Clear files that should never be deployed
    local('rm -rf %s/live-data' % path)
    local('rm -rf %s/sitemap.xml' % path)

    exclude_flags = ''
    include_flags = ''

    with open('gzip_types.txt') as f:
        for line in f:
            exclude_flags += '--exclude "%s" ' % line.strip()
            include_flags += '--include "%s" ' % line.strip()

    exclude_flags += '--exclude "www/assets" '

    sync = 'aws s3 sync --quiet %s/ %s --acl "public-read" ' + exclude_flags + ' --cache-control "max-age=%i no-cache no-store must-revalidate" --region "%s"'
    sync_gzip = 'aws s3 sync --quiet %s/ %s --acl "public-read" --content-encoding "gzip" --exclude "*" ' + include_flags + ' --cache-control "max-age=%i no-cache no-store must-revalidate" --region "%s"'
    sync_assets = 'aws s3 sync --quiet %s/ %s --acl "public-read" --cache-control "max-age=86400" --region "%s"'

    for bucket in app_config.S3_BUCKETS:
        local(sync % (path, 's3://%s/' % bucket['bucket_name'], app_config.MAX_AGE_CACHE_CONTROL_HEADER, bucket['region']))
        local(sync_gzip % (path, 's3://%s/' % bucket['bucket_name'], app_config.MAX_AGE_CACHE_CONTROL_HEADER, bucket['region']))
        local(sync_assets % ('www/assets/', 's3://%s/assets/' % (bucket['bucket_name']), bucket['region']))

def deploy_json(src, dst):
    """
    Deploy the gzipped stuff to S3.
    """
    sync = 'aws s3 cp %s %s --acl "public-read" --cache-control "max-age=5 no-cache no-store must-revalidate" --region "%s"'

    for bucket in app_config.S3_BUCKETS:
        local(sync % (src, 's3://%s/%s' % (bucket['bucket_name'], dst), bucket['region']))
