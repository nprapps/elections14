#!/usr/bin/env python

from time import sleep, time
from fabric.api import execute, task, env

import app_config
import sys
import traceback

def safe_execute(*args, **kwargs):
    """
    Wrap execute() so that all exceptions are caught and logged.
    """
    try:
        execute(*args, **kwargs)
    except:
        print "ERROR [timestamp: %d]: Here's the traceback" % time()
        ex_type, ex, tb = sys.exc_info()
        traceback.print_tb(tb)
        del tb

@task
def deploy():
    """
    Harvest data and deploy slides indefinitely
    """
    while True:
        start = time()
        safe_execute('ap.update')
        safe_execute('data.load_updates', 'data/update.json')
        safe_execute('liveblog.update')
        safe_execute('deploy_slides')
        safe_execute('deploy_big_boards')

        duration = int(time() - start)
        wait = app_config.DEPLOY_INTERVAL - duration

        print "== Deploying slides ran in %ds, waiting %ds ==" % (duration, wait)

        if wait < 0:
            print "WARN: Deploying slides took %d seconds longer than %d" % (abs(wait), app_config.DEPLOY_INTERVAL)
            wait = 0

        sleep(wait)
