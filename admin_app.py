#!/usr/bin/env python

import argparse
import datetime
import logging

from flask import Flask, render_template
from flask_peewee.auth import Auth
from flask_peewee.db import Database
from flask_peewee.admin import Admin, ModelAdmin
from models import Slide, SlideSequence

import app_config
from render_utils import make_context
import static

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['DATABASE'] = app_config.DATABASE
app.config['SECRET_KEY'] = 'askfhj3r3j'

file_handler = logging.FileHandler(app_config.APP_LOG_PATH)
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

class SlideAdmin(ModelAdmin):
    exclude = ('slug',)

# Set up flask peewee db wrapper
db = Database(app)
auth = Auth(app, db, prefix='/%s/accounts' % app_config.PROJECT_SLUG)
admin = Admin(app, auth, prefix='/%s/admin' % app_config.PROJECT_SLUG)
admin.register(Slide, SlideAdmin)
admin.register(SlideSequence)
admin.setup()

# Example application views
@app.route('/%s/test/' % app_config.PROJECT_SLUG, methods=['GET'])
def _test_app():
    """
    Test route for verifying the application is running.
    """
    app.logger.info('Test URL requested.')

    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Example of rendering HTML with the rig
import static
from render_utils import urlencode_filter

app.register_blueprint(static.static, url_prefix='/%s' % app_config.PROJECT_SLUG)
app.jinja_env.filters['urlencode'] = urlencode_filter

@app.route('/%s/stack/' % app_config.PROJECT_SLUG, methods=['GET'])
def stack():
    """
    Administer a stack of slides.
    """
    context = make_context()
    context.update({
        'sequence': SlideSequence.select().dicts(),
        'slides': Slide.select().dicts(),
    })
    return render_template('stack_admin.html', **context)

@app.route('/%s/stack/save' % app_config.PROJECT_SLUG, methods=['POST'])
def save_stack():
    from flask import request
    data = request.json
    SlideSequence.delete().execute()
    # rebuild sequence table
    for i, row in enumerate(data[0]):
        obj = SlideSequence(slide=row["slide"], sequence = i + 1)
        obj.save()
    return "saved sequence"

app.register_blueprint(static.static)

# Boilerplate
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port')
    args = parser.parse_args()
    server_port = 8080

    if args.port:
        server_port = int(args.port)

    app.run(host='0.0.0.0', port=server_port, debug=app_config.DEBUG)
