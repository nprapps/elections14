#!/usr/bin/env python

import argparse
import datetime
import logging

from flask import Flask, render_template, request
from flask_peewee.auth import Auth
from flask_peewee.db import Database
from flask_peewee.admin import Admin, ModelAdmin
from models import Slide, SlideSequence, Race, Candidate

import app_config
from render_utils import make_context, CSSIncluder, JavascriptIncluder, urlencode_filter
import static_app

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['DATABASE'] = app_config.DATABASE
app.config['SECRET_KEY'] = 'askfhj3r3j'

app.jinja_env.filters['urlencode'] = urlencode_filter
app.register_blueprint(static_app.static_app, url_prefix='/%s' % app_config.PROJECT_SLUG)

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

@app.route('/%s/stack/' % app_config.PROJECT_SLUG, methods=['GET'])
def stack():
    """
    Administer a stack of slides.
    """
    context = make_context(asset_depth=1)
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

@app.route('/%s/chamber/<chamber>/' % app_config.PROJECT_SLUG, methods=['GET', 'POST'])
def chamber(chamber):
    """
    Read/update list of chamber candidates.
    """

    chamber_slug = u'H'
    if chamber == 'senate':
        chamber_slug = u'S'

    if request.method == 'GET':

        # Get all of the candidates that match this race which are either
        # Republicans or Democrats or have the first name Angus or Bernie and
        # we ignore the Democrat in the Maine race.
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
                Candidate.party.asc())

        race_count = Race.select().where(Race.office_id == chamber_slug)

        context = make_context(asset_depth=1)

        context.update({
            'candidates': candidates,
            'count': race_count.count(),
            'chamber': chamber,
        })

        return render_template('admin/chamber.html', **context)

    # Alternately, what if someone is POSTing?
    if request.method == 'POST':

        # Everything needs a race slug.
        race_slug = request.form.get('race_slug', None)
        race = Race.select().where(Race.slug == race_slug).get()

        # 1.) Perhaps we're trying to set the accept_ap_call flag on some races?
        accept_ap_call = request.form.get('accept_ap_call', None)

        if accept_ap_call != None:
            if accept_ap_call.lower() == 'true':
                accept_ap_call = True
            else:
                accept_ap_call = False

        if race_slug != None and accept_ap_call != None:
            aq = Race.update(accept_ap_call=accept_ap_call).where(Race.slug == race.slug)
            aq.execute()

            if accept_ap_call == True:
                rq = Candidate.update(npr_winner=False).where(Candidate.race == race)
                rq.execute()

        # 2.) Perhaps we're trying to set an NPR winner?
        first_name = request.form.get('first_name', None)
        last_name = request.form.get('last_name', None)
        clear_all = request.form.get('clear_all', None)

        if race_slug != None and clear_all != None:
            if clear_all == 'true':
                rq = Candidate.update(npr_winner=False).where(Candidate.race == race)
                rq.execute()

                rq2 = Race.update(npr_called=False).where(Race.slug == race_slug)
                rq2.execute()

        if race_slug != None and first_name != None and last_name != None:

            rq = Candidate.update(npr_winner=False).where(Candidate.race == race)
            rq.execute()

            cq = Candidate.update(npr_winner=True).where(
                Candidate.race == race,
                Candidate.first_name == first_name,
                Candidate.last_name == last_name)
            cq.execute()

            race_update = {}
            race_update['npr_called'] = True
            if race.accept_ap_call == False:
                if race.npr_called_time == None:
                    race_update['npr_called_time'] = datetime.datetime.utcnow()

            rq2 = Race.update(**race_update).where(Race.slug == race_slug)
            rq2.execute()

        # TODO
        # Return a 200. This is probably bad.
        # Need to figure out what should go here.
        return "Success."


# Boilerplate
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port')
    args = parser.parse_args()
    server_port = 8080

    if args.port:
        server_port = int(args.port)

    app.run(host='0.0.0.0', port=server_port, debug=app_config.DEBUG)
