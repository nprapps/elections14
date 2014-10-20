#!/usr/bin/env python

import argparse
import datetime
import logging
import subprocess

from flask import Flask, render_template, send_file
from flask_peewee.auth import Auth
from flask_peewee.db import Database
from flask_peewee.admin import Admin, ModelAdmin
from models import Slide, SlideSequence, Race, Candidate
from peewee import fn

import app_config
from render_utils import make_context, urlencode_filter, smarty_filter
import static_app

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['DATABASE'] = app_config.DATABASE
app.config['SECRET_KEY'] = 'askfhj3r3j'

app.jinja_env.filters['urlencode'] = urlencode_filter
app.jinja_env.filters['smarty'] = smarty_filter
app.register_blueprint(static_app.static_app, url_prefix='/%s' % app_config.PROJECT_SLUG)

file_handler = logging.FileHandler('%s/app.log' % app_config.SERVER_LOG_PATH)
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

@app.route('/%s/admin/stack/' % app_config.PROJECT_SLUG, methods=['GET'])
def stack():
    """
    Administer a stack of slides.
    """
    context = make_context(asset_depth=1)

    sequence = SlideSequence.select()

    time = 0

    for slide in sequence:
        time += slide.slide.time_on_screen

    context.update({
        'sequence': SlideSequence.select().dicts(),
        'slides': Slide.select().dicts(),
        'graphics': Slide.select().where(fn.Lower(fn.Substr(Slide.slug, 1, 6)) != 'tumblr').order_by(Slide.slug).dicts(),
        'news':  Slide.select().where(fn.Lower(fn.Substr(Slide.slug, 1, 6)) == 'tumblr').order_by(Slide.slug).dicts(),
        'time': time,
    })

    return render_template('admin/stack.html', **context)

@app.route('/%s/admin/stack/share/<slug>' % app_config.PROJECT_SLUG, methods=['GET'])
def share(slug):
    preview_url = '%s/preview/%s' % (app_config.S3_BASE_URL, slug)
    image_url = 'www/assets/share-images/%s.png' % slug

    subprocess.check_output([
        "node_modules/depict/src/depict.js",
        preview_url,
        image_url,
        '--call-phantom',
    ])

    response = send_file(image_url, mimetype='image/png')
    response.headers['Content-Disposition'] = 'attachment'
    return response


@app.route('/%s/admin/stack/save' % app_config.PROJECT_SLUG, methods=['POST'])
def save_stack():
    """
    Save new stack sequence.
    """
    from flask import request

    data = request.json
    SlideSequence.delete().execute()

    # Rebuild sequence table
    for i, row in enumerate(data[0]):
        SlideSequence.create(order=i, slide=row['slide'])

    return "Saved sequence"

@app.route('/%s/admin/chamber/<chamber>/' % app_config.PROJECT_SLUG, methods=['GET'])
def chamber(chamber):
    """
    Read/update list of chamber candidates.
    """
    chamber_slug = 'H'

    if chamber == 'senate':
        chamber_slug = 'S'

    elif chamber == 'governor':
        chamber_slug = 'G'

    # TODO: special cases for independents who might win
    candidates = Candidate\
        .select()\
        .join(Race)\
        .where(
            Race.office_id == chamber_slug,
            (Candidate.party == 'Dem') | (Candidate.party == 'GOP')
        )

    candidates = candidates.order_by(
        Race.state_postal.desc(),
        Race.seat_number.asc(),
        Candidate.party.asc()
    )

    race_count = Race.select().where(Race.office_id == chamber_slug)

    context = make_context(asset_depth=1)

    context.update({
        'candidates': candidates,
        'count': race_count.count(),
        'chamber': chamber,
    })

    return render_template('admin/chamber.html', **context)

@app.route('/%s/admin/chamber/<chamber>/call/' % app_config.PROJECT_SLUG, methods=['POST'])
def chamber_call(chamber):
    from flask import request

    race_slug = request.form.get('race_slug', None)

    race = Race.get(Race.slug == race_slug)

    # Toggling accept AP call
    accept_ap_call = request.form.get('accept_ap_call', None)

    if accept_ap_call != None:
        if accept_ap_call.lower() == 'true':
            accept_ap_call = True
        else:
            accept_ap_call = False

    if race_slug != None and accept_ap_call != None:
        race.accept_ap_call = accept_ap_call
        race.save()

        if accept_ap_call == True:
            Candidate.update(npr_winner=False).where(Candidate.race == race).execute()

    # Setting NPR winner
    first_name = request.form.get('first_name', None)
    last_name = request.form.get('last_name', None)
    clear_all = request.form.get('clear_all', None)

    if race_slug != None and clear_all != None:
        if clear_all == 'true':
            Candidate.update(npr_winner=False).where(Candidate.race == race).execute()

            race.npr_called = False
            race.save()

    if race_slug != None and first_name != None and last_name != None:
        Candidate.update(npr_winner=False).where(Candidate.race == race).execute()

        Candidate.update(npr_winner=True).where(
            Candidate.race == race,
            Candidate.first_name == first_name,
            Candidate.last_name == last_name
        ).execute()

        race.npr_called = True

        if race.accept_ap_call == False:
            if race.npr_called_time == None:
                race.npr_called_time = datetime.datetime.utcnow()

        race.save()

    return 'Success'

# Boilerplate
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port')
    args = parser.parse_args()
    server_port = 8080

    if args.port:
        server_port = int(args.port)

    app.run(host='0.0.0.0', port=server_port, debug=app_config.DEBUG)
