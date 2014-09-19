#!/usr/bin/env python

from time import sleep

from fabric.api import execute, task

@task
def tumblr():
    while True:
        execute('tumblr.get_posts')
        execute('deploy_slides')
        sleep(30)

@task
def rotate_slide():
    while True:
        execute('stack.rotate')
        sleep(15)
