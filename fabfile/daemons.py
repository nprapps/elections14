#!/usr/bin/env python

from time import sleep

from fabric.api import task

import cron_jobs
import tumblr

@task
def tumblr():
    while True:
        tumblr.get_posts()
        sleep(15)

@task
def rotate_slide():
    while True:
        cron_jobs.rotate_slide()
        sleep(15)
