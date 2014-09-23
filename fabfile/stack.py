#!/usr/bin/env python

import json

from fabric.api import env, local, require, task
from peewee import fn

import app_config
from models import SlideSequence
from utils import deploy_json

STACK_NUMBER_FILENAME = '.stack_number'

@task
def rotate():
    """
    Rotate to the next slide in the sequence.
    """
    require('settings', provided_by=['production', 'staging'])

    min_sequence = SlideSequence.select(fn.Min(SlideSequence.sequence)).scalar()

    try:
        with open(STACK_NUMBER_FILENAME, 'r') as f:
            sequence = int(f.read().strip())
    except IOError:
        sequence = min_sequence

    next_slide = SlideSequence.select().where(SlideSequence.sequence > sequence).order_by(SlideSequence.sequence.asc()).limit(1)

    if next_slide.count():
        next_slide = next_slide[0]
    else:
        next_slide = SlideSequence.get(SlideSequence.sequence==min_sequence)

    with open('www/%s' % app_config.NEXT_SLIDE_FILENAME, 'w') as f:
        json.dump({
            'next': 'slides/%s.html' % next_slide.slide.slug,
        }, f)

    with open(STACK_NUMBER_FILENAME, 'w') as f:
        f.write(unicode(next_slide.sequence))

    if env.settings:
        deploy_json(
            'www/%s' % app_config.NEXT_SLIDE_FILENAME,
            app_config.NEXT_SLIDE_FILENAME
        )
