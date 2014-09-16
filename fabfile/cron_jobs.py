#!/usr/bin/env python

"""
Cron jobs
"""
import json

from fabric.api import env, local, require, task

import app_config
from models import SlideSequence
from utils import deploy_json

STACK_NUMBER_FILENAME = '.stack_number'

@task
def rotate_slide():
    """
    Rotate to the next slide in the sequence.
    """
    require('settings', provided_by=['production', 'staging'])

    try:
        with open(STACK_NUMBER_FILENAME, 'r') as f:
            stack_number = int(f.read().strip())
    except IOError:
        stack_number = 0 

    slides = SlideSequence.select().count()

    if stack_number == slides:
        stack_number = 0 

    stack_number += 1
    next_slide = SlideSequence.get(SlideSequence.sequence == stack_number)

    with open('www/%s' % app_config.NEXT_SLIDE_FILENAME, 'w') as f:
        json.dump({
            'next': '/slides/%s.html' % next_slide.slide.__unicode__(),
        }, f)

    with open(STACK_NUMBER_FILENAME, 'w') as f:
        f.write(unicode(stack_number))

    if env.settings:
        deploy_json(
            'www/%s' % app_config.NEXT_SLIDE_FILENAME,
            app_config.NEXT_SLIDE_FILENAME
        )

@task
def test():
    """
    Example cron task. Note we use "local" instead of "run"
    because this will run on the server.
    """
    require('settings', provided_by=['production', 'staging'])

    local('echo $DEPLOYMENT_TARGET > /tmp/cron_test.txt')

