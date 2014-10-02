#!/usr/bin/env python

from time import sleep

from fabric.api import execute, task

import app_config

@task
def liveblog():
    """
    Fetch new Tumblr posts indenfinitely.
    """
    while True:
        execute('liveblog.update')
        execute('deploy_slides')
        sleep(app_config.TUMBLR_REFRESH_INTERVAL)

@task
def stack():
    """
    Rotate slides indenfinitely.
    """
    while True:
        execute('stack.update')
        sleep(app_config.STACK_UPDATE_INTERVAL)

@task
def instagram():
    """
    Get photos from Instagram callout indefinitely.
    """
    while True:
        execute('instagram.get_photos')
        execute('deploy_instagram_photos')
        execute('deploy_slides')
        sleep(app_config.INSTAGRAM_REFRESH_INTERVAL)
