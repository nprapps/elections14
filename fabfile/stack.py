#!/usr/bin/env python

import json

from fabric.api import env, local, require, task
from peewee import fn

import app
import app_config
from models import SlideSequence
from utils import deploy_json

@task
def rotate():
    """
    Rotate to the next slide in the sequence.
    """
    require('settings', provided_by=['production', 'staging'])

    next_slide = app.rotate_slide()

    with open('www/%s' % app_config.NEXT_SLIDE_FILENAME, 'w') as f:
        json.dump({
            'next': 'slides/%s.html' % next_slide.slide.slug,
        }, f)

    if env.settings:
        deploy_json(
            'www/%s' % app_config.NEXT_SLIDE_FILENAME,
            app_config.NEXT_SLIDE_FILENAME
        )
