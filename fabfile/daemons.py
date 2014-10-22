#!/usr/bin/env python

from time import sleep

from fabric.api import execute, task

import app_config

@task
def liveblog():
    """
    Fetch new Tumblr posts indefinitely.
    """
    while True:
        execute('liveblog.update')
        execute('deploy_slides')
        sleep(app_config.TUMBLR_REFRESH_INTERVAL)

@task
def stack():
    """
    Rotate slides indefinitely.
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

@task
def results():
    """
    Fetch results indefinitely.
    """
    while True:
        execute('ap.update')
        execute('data.load_updates', 'data/update.json')
        execute('deploy_slides')
        execute('deploy_big_boards')
        sleep(app_config.AP_RESULTS_REFRESH_INTERVAL)
