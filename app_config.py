#!/usr/bin/env python

"""
Project-wide application configuration.

DO NOT STORE SECRETS, PASSWORDS, ETC. IN THIS FILE.
They will be exposed to users. Use environment variables instead.
See get_secrets() below for a fast way to access them.
"""

from datetime import datetime
import os

"""
NAMES
"""
# Project name to be used in urls
# Use dashes, not underscores!
PROJECT_SLUG = 'elections14'

# Project name to be used in file paths
PROJECT_FILENAME = 'elections14'

# The name of the repository containing the source
REPOSITORY_NAME = 'elections14'
GITHUB_USERNAME = 'nprapps'
REPOSITORY_URL = 'git@github.com:%s/%s.git' % (GITHUB_USERNAME, REPOSITORY_NAME)
REPOSITORY_ALT_URL = None # 'git@bitbucket.org:nprapps/%s.git' % REPOSITORY_NAME'

# Project name used for assets rig
# Should stay the same, even if PROJECT_SLUG changes
ASSETS_SLUG = 'elections14'

"""
DEPLOYMENT
"""
PRODUCTION_S3_BUCKETS = [
    {
        'bucket_name': 'elections.npr.org',
        'region': 'us-west-2'
    }
]

STAGING_S3_BUCKETS = [
    {
        'bucket_name': 'stage-elections14',
        'region': 'us-east-1'
    }
]

ASSETS_S3_BUCKET = {
    'bucket_name': 'assets.apps.npr.org',
    'region': 'us-east-1'
}

PRODUCTION_SERVERS = ['54.244.238.237']
STAGING_SERVERS = ['54.244.238.154']

# Should code be deployed to the web/cron servers?
DEPLOY_TO_SERVERS = True

SERVER_USER = 'ubuntu'
SERVER_PYTHON = 'python2.7'
SERVER_PROJECT_PATH = '/home/%s/apps/%s' % (SERVER_USER, PROJECT_FILENAME)
SERVER_REPOSITORY_PATH = '%s/repository' % SERVER_PROJECT_PATH
SERVER_VIRTUALENV_PATH = '%s/virtualenv' % SERVER_PROJECT_PATH

# Should the crontab file be installed on the servers?
# If True, DEPLOY_TO_SERVERS must also be True
DEPLOY_CRONTAB = True

# Should the service configurations be installed on the servers?
# If True, DEPLOY_TO_SERVERS must also be True
DEPLOY_SERVICES = True

UWSGI_SOCKET_PATH = '/tmp/%s.uwsgi.sock' % PROJECT_FILENAME

# Services are the server-side services we want to enable and configure.
# A three-tuple following this format:
# (service name, service deployment path, service config file extension)
SERVER_SERVICES = [
    ('app', SERVER_REPOSITORY_PATH, 'ini'),
    ('uwsgi', '/etc/init', 'conf'),
    ('nginx', '/etc/nginx/locations-enabled', 'conf'),
    ('deploy', '/etc/init', 'conf'),
]

# These variables will be set at runtime. See configure_targets() below
S3_BUCKETS = []
S3_BASE_URL = ''
SERVERS = []
SERVER_BASE_URL = ''
SERVER_LOG_PATH = ''
DEBUG = True

"""
COPY EDITING
"""
COPY_GOOGLE_DOC_URL = 'https://docs.google.com/spreadsheet/ccc?key=0AlXMOHKxzQVRdF9HTzlTeEJWV3hUbWFBODlPcVdnSGc'
COPY_PATH = 'data/copy.xlsx'

"""
SHARING
"""
SHARE_URL = 'http://%s/%s/' % (PRODUCTION_S3_BUCKETS[0], PROJECT_SLUG)

"""
ADS
"""

NPR_DFP = {
    'STORY_ID': '1002',
    'TARGET': 'homepage',
    'ENVIRONMENT': 'NPRTEST',
    'TESTSERVER': 'false'
}

"""
SERVICES
"""
GOOGLE_ANALYTICS = {
    'ACCOUNT_ID': 'UA-5828686-4',
    'DOMAIN': PRODUCTION_S3_BUCKETS[0],
    'TOPICS': '' # e.g. '[1014,3,1003,1002,1001]'
}

DISQUS_API_KEY = 'tIbSzEhGBE9NIptbnQWn4wy1gZ546CsQ2IHHtxJiYAceyyPoAkDkVnQfCifmCaQW'
DISQUS_UUID = '187d5a38-3768-11e4-8de3-14109fed4b76'

DEPLOY_PROMO = False

CHROMECAST_APP_ID = '8408F716'
CHROMECAST_NAMESPACE = 'urn:x-cast:nprviz.elections14'

SLIDE_ROTATE_INTERVAL = 5
STACK_UPDATE_INTERVAL = 60

TUMBLR_NAME = '' # See below
TUMBLR_NOT_BEFORE = None # See below
TUMBLR_AUTO_REFRESH = None # See below

DEPLOY_INTERVAL = 60

STATES = {
    'AK': 'Alaska',
    'AL': 'Alabama',
    'AR': 'Arkansas',
    'AZ': 'Arizona',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DC': 'District of Columbia',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'HI': 'Hawaii',
    'IA': 'Iowa',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'MA': 'Massachusetts',
    'MD': 'Maryland',
    'ME': 'Maine',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MO': 'Missouri',
    'MS': 'Mississippi',
    'MT': 'Montana',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'NE': 'Nebraska',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NV': 'Nevada',
    'NY': 'New York',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VA': 'Virginia',
    'VT': 'Vermont',
    'WA': 'Washington',
    'WI': 'Wisconsin',
    'WV': 'West Virginia',
    'WY': 'Wyoming',
}

# States with many results that need to be paginated
PAGINATED_STATES = [
    'CA',
    'IL',
    'NY'
]

"""
Utilities
"""
def get_secrets():
    """
    A method for accessing our secrets.
    """
    secrets = [
        'ADMIN_PASSWORD',
        'AP_API_KEY',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'POSTGRES_HOST',
        'POSTGRES_PORT',
        'TUMBLR_CONSUMER_KEY'
    ]

    secrets_dict = {}

    for secret in secrets:
        name = '%s_%s' % (PROJECT_FILENAME, secret)
        secrets_dict[secret] = os.environ.get(name, None)

    return secrets_dict

def configure_targets(deployment_target):
    """
    Configure deployment targets. Abstracted so this can be
    overriden for rendering before deployment.
    """
    global DEPLOYMENT_TARGET
    global S3_BUCKETS
    global S3_BASE_URL
    global SERVERS
    global SERVER_BASE_URL
    global SERVER_LOG_PATH
    global DEBUG
    global DISQUS_SHORTNAME
    global TUMBLR_NAME
    global TUMBLR_AUTO_REFRESH
    global TUMBLR_NOT_BEFORE

    if deployment_target == 'production':
        S3_BUCKETS = PRODUCTION_S3_BUCKETS
        S3_BASE_URL = 'http://%s' % (S3_BUCKETS[0]['bucket_name'])
        SERVERS = PRODUCTION_SERVERS
        SERVER_BASE_URL = 'http://%s/%s' % (SERVERS[0], PROJECT_SLUG)
        SERVER_LOG_PATH = '/var/log/%s' % PROJECT_FILENAME
        DEBUG = False

        DISQUS_SHORTNAME = 'npr-news'

        TUMBLR_NAME = 'nprpolitics'
        TUMBLR_AUTO_REFRESH = False
        TUMBLR_NOT_BEFORE = datetime(2014, 11, 4, 23, 0, 0) # +5 hours for UTC
    elif deployment_target == 'staging':
        S3_BUCKETS = STAGING_S3_BUCKETS
        S3_BASE_URL = '//d3dhid83frmf6i.cloudfront.net'
        SERVERS = STAGING_SERVERS
        SERVER_BASE_URL = 'http://%s/%s' % (SERVERS[0], PROJECT_SLUG)
        SERVER_LOG_PATH = '/var/log/%s' % PROJECT_FILENAME
        DEBUG = True

        DISQUS_SHORTNAME = 'nprviz-test'

        TUMBLR_NAME = 'stage-nprelections'
        TUMBLR_AUTO_REFRESH = True
        TUMBLR_NOT_BEFORE = datetime(2014, 10, 7, 11, 0, 0)
    else:
        S3_BUCKETS = []
        S3_BASE_URL = 'http://127.0.0.1:8000'
        SERVERS = []
        SERVER_BASE_URL = 'http://127.0.0.1:8080/%s' % PROJECT_SLUG
        SERVER_LOG_PATH = '/tmp'
        DEBUG = True

        DISQUS_SHORTNAME = 'nprviz-test'

        TUMBLR_NAME = 'stage-nprelections'
        TUMBLR_AUTO_REFRESH = True
        TUMBLR_NOT_BEFORE = datetime(2014, 9, 26, 0, 0, 0)

    DEPLOYMENT_TARGET = deployment_target

"""
Run automated configuration
"""
DEPLOYMENT_TARGET = os.environ.get('DEPLOYMENT_TARGET', None)

configure_targets(DEPLOYMENT_TARGET)


"""
Database
"""
secrets = get_secrets()
DATABASE = {
    'name': PROJECT_SLUG,
    'user': secrets.get('POSTGRES_USER', None),
    'engine': 'peewee.PostgresqlDatabase',
    'password': secrets.get('POSTGRES_PASSWORD', None),
    'host': secrets.get('POSTGRES_HOST', 'localhost'),
    'port': secrets.get('POSTGRES_PORT', 5432)
}

