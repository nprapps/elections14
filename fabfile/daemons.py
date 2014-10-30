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
def deploy_liveblog():
    """
    Get and update liveblog slides
    """
    while True:
        start = time()
        safe_execute('liveblog.update')
        safe_execute('deploy_liveblog_slides')
        duration = int(time() - start)
        wait = app_config.LIVEBLOG_DEPLOY_INTERVAL - duration

        if wait < 0:
            print "== WARN: Deploying slides took %d seconds longer than %d ==" % (abs(wait), app_config.LIVEBLOG_DEPLOY_INTERVAL)
            wait = 0
        else:
            print "== Deploying slides ran in %ds, waiting %ds ==" % (duration, wait)

        sleep(wait)

@task
def deploy_results():
    """
    Harvest data and deploy slides indefinitely
    """
    while True:
        start = time()
        next = start
        safe_execute('ap.update')
        print "AP update took %d seconds" % (time() - next)

        next = time()
        safe_execute('data.update')
        print "Data update took %d seconds" % (time() - next)

        next = time()
        safe_execute('deploy_bop')
        print "Deploying BOP took %d seconds" % (time() - next)

        next = time()
        safe_execute('deploy_big_boards')
        print "Deploying big boards took %d seconds" % (time() - next)

        next = time()
        safe_execute('deploy_results_slides')
        print "Deploying results took %d seconds" % (time() - next)

        duration = int(time() - start)
        wait = app_config.RESULTS_DEPLOY_INTERVAL - duration


        if wait < 0:
            print "WARN: Deploying slides took %ds longer than %ds" % (abs(wait), app_config.RESULTS_DEPLOY_INTERVAL)
            wait = 0
        else:
            print "== Deploying slides ran in %ds, waiting %ds ==" % (duration, wait)

        sleep(wait)
