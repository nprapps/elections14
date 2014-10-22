#!/usr/bin/env python

from time import sleep, time
from fabric.api import execute, task, env

import app_config
import sys
import traceback

def safe_execute(*args, **kwargs):
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
        safe_execute('ap.update')
        safe_execute('data.load_updates', 'data/update.json')
        safe_execute('liveblog.update')
        safe_execute('deploy_slides')
        safe_execute('deploy_big_boards')
        sleep(app_config.DEPLOY_INTERVAL)
