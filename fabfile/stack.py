#!/usr/bin/env python

import json

from fabric.api import env, require, task

from utils import deploy_json

@task
def update():
    """
    Rotate to the next slide in the sequence.
    """
    require('settings', provided_by=['production', 'staging'])

    from models import SlideSequence

    data = SlideSequence.stack()

    print 'Updating stack'

    with open('www/live-data/stack.json', 'w') as f:
        json.dump(data, f)

    if env.settings:
        deploy_json(
            'www/live-data/stack.json',
            'live-data/stack.json'
        )