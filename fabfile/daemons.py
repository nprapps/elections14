#!/usr/bin/env python

from time import sleep

from fabric.api import execute, task

import app_config

@task
def tumblr():
    while True:
        execute('tumblr.get_posts')
        execute('deploy_slides')
        sleep(app_config.TUMBLR_REFRESH_INTERVAL)

@task
def rotate_slide():
    while True:
        execute('stack.rotate')
        sleep(app_config.SLIDE_ROTATE_INTERVAL)
