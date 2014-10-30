#!/usr/bin/env python
from datetime import datetime
import json

from fabric.api import local, require, settings, task
from fabric.state import env
from termcolor import colored

import app_config

# Other fabfiles
import ap
import assets
import daemons
import data
import instagram
import issues
import liveblog
import render
import stack
import text
import theme
import utils

if app_config.DEPLOY_TO_SERVERS:
    import servers

if app_config.DEPLOY_CRONTAB:
    import cron_jobs

# Bootstrap can only be run once, then it's disabled
if app_config.PROJECT_SLUG == '$NEW_PROJECT_SLUG':
    import bootstrap

"""
Base configuration
"""
env.user = app_config.SERVER_USER
env.forward_agent = True

env.hosts = []
env.settings = None

"""
Environments

Changing environment requires a full-stack test.
An environment points to both a server and an S3
bucket.
"""
@task
def production():
    """
    Run as though on production.
    """
    env.settings = 'production'
    app_config.configure_targets(env.settings)
    env.hosts = app_config.SERVERS

@task
def staging():
    """
    Run as though on staging.
    """
    env.settings = 'staging'
    app_config.configure_targets(env.settings)
    env.hosts = app_config.SERVERS

"""
Branches

Changing branches requires deploying that branch to a host.
"""
@task
def stable():
    """
    Work on stable branch.
    """
    env.branch = 'stable'

@task
def master():
    """
    Work on development branch.
    """
    env.branch = 'master'

@task
def branch(branch_name):
    """
    Work on any specified branch.
    """
    env.branch = branch_name

@task
def tests():
    """
    Run Python unit tests.
    """
    with settings(warn_only=True):
        local('createdb elections14test')

    local('nosetests')


"""
Deployment

Changes to deployment requires a full-stack test. Deployment
has two primary functions: Pushing flat files to S3 and deploying
code to a remote server if required.
"""
@task
def update():
    """
    Update all application data not in repository (copy, assets, etc).
    """
    text.update()
    assets.sync()
    #data.update()

@task
def deploy_server(remote='origin'):
    """
    Deploy server code and configuration.
    """
    if app_config.DEPLOY_TO_SERVERS:
        require('branch', provided_by=[stable, master, branch])

        if (app_config.DEPLOYMENT_TARGET == 'production' and env.branch != 'stable'):
            utils.confirm(
                colored("You are trying to deploy the '%s' branch to production.\nYou should really only deploy a stable branch.\nDo you know what you're doing?" % env.branch, "red")
            )

        servers.checkout_latest(remote)

        servers.fabcast('text.update')
        servers.fabcast('assets.sync')

        if app_config.DEPLOY_CRONTAB:
            servers.install_crontab()

        if app_config.DEPLOY_SERVICES:
            servers.deploy_confs()

@task
def deploy_client(remote='origin'):
    """
    Render and deploy app to S3.
    """
    require('settings', provided_by=[production, staging])

    update()
    render.render_all()
    utils._gzip('www', '.gzip')
    utils._deploy_to_s3()

@task
def deploy_liveblog_slides():
    """
    Deploy latest liveblog slides to S3.
    """
    local('rm -rf .liveblog_slides_html .liveblog_slides_gzip')
    render.render_liveblog_slides()
    utils._gzip('.liveblog_slides_html', '.liveblog_slides_gzip')
    utils._deploy_to_s3('.liveblog_slides_gzip')

@task
def deploy_results_slides():
    """
    Deploy latest results slides to S3.
    """
    local('rm -rf .results_slides_html .results_slides_gzip')
    render.render_results_slides()
    utils._gzip('.results_slides_html', '.results_slides_gzip')
    utils._deploy_to_s3('.results_slides_gzip')

@task
def deploy_big_boards():
    """
    Deploy big boards to S3.
    """
    local('rm -rf .big_boards_html .big_boards_gzip')
    render.render_big_boards()
    utils._gzip('.big_boards_html', '.big_boards_gzip')
    utils._deploy_to_s3('.big_boards_gzip')

@task
def deploy_bop():
    """
    Deploy latest BOP.
    """
    local('rm -rf .bop_html .bop_gzip')
    render.render_bop()
    utils._gzip('.bop_html', '.bop_gzip')
    utils._deploy_to_s3('.bop_gzip')

@task
def deploy():
    """
    Deploy the latest app to S3 and, if configured, to our servers.
    """
    require('settings', provided_by=[production, staging])

    deploy_server()
    deploy_client()

@task
def reset_browsers():
    """
    Deploy a timestamp so the client will reset their page. For bugfixes
    """
    require('settings', provided_by=[production, staging])

    now = datetime.now()

    with open('www/live-data/timestamp.json', 'w') as f:
        json.dump(now.isoformat(), f)

    utils.deploy_json('www/live-data/timestamp.json', 'live-data/timestamp.json')

"""
Destruction

Changes to destruction require setup/deploy to a test host in order to test.
Destruction should remove all files related to the project from both a remote
host and S3.
"""

@task
def shiva_the_destroyer():
    """
    Deletes the app from s3
    """
    require('settings', provided_by=[production, staging])

    utils.confirm(
        colored("You are about to destroy everything deployed to %s for this project.\nDo you know what you're doing?')" % app_config.DEPLOYMENT_TARGET, "red")
    )

    with settings(warn_only=True):
        sync = 'aws s3 rm %s --recursive --region "%s"'

        for bucket in app_config.S3_BUCKETS:
            local(sync % ('s3://%s/' % bucket['bucket_name'], bucket['region']))

        if app_config.DEPLOY_TO_SERVERS:
            servers.delete_project()

            if app_config.DEPLOY_CRONTAB:
                servers.uninstall_crontab()

            if app_config.DEPLOY_SERVICES:
                servers.nuke_confs()

