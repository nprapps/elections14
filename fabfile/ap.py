#!/usr/bin/env python

import app_config
import json
import os
import time

from datetime import datetime
from elections import AP
from fabric.api import task
from time import sleep

SECRETS = app_config.get_secrets()

def _generate_candidate_id(candidate, race):
    """
    Makes an unique compound ID
    """
    return '%s-%s' % (candidate.ap_polra_number, race.state_postal)

@task
def bootstrap():
    init()
    update()

@task
def init(output_dir='data'):
    """
    Initialize data from AP.
    """
    client = AP(SECRETS['AP_FTP_USER'], SECRETS['AP_FTP_PASSWORD'])
    ticket = client.get_topofticket('2014-11-04')

    races = []
    candidates = []

    for race in ticket.races:
        races.append(process_race(race))

        for candidate in race.candidates:
            candidates.append(process_candidate(candidate, race))

    with open('%s/init_races.json' % output_dir, 'w') as f:
        json.dump(races, f, indent=4)

    with open('%s/init_candidates.json' % output_dir, 'w') as f:
        json.dump(candidates, f, indent=4)

@task
def update(output_dir='data'):
    """
    Update data from AP.
    """
    client = AP(SECRETS['AP_FTP_USER'], SECRETS['AP_FTP_PASSWORD'])
    ticket = client.get_topofticket('2014-11-04')

    write_update(ticket, '%s/update.json' % output_dir)
    write_calls(ticket, '%s/calls.json' % output_dir)


def process_race(race):
    """
    Process a single race into our intermediary format.
    """
    ret = {
        'state_postal': race.state_postal,
        'office_id': race.office_id,
        'office_name': race.office_name,
        'seat_name': race.seat_name,
        'seat_number': race.seat_number,
        'race_id': race.ap_race_number,
        'race_type': race.race_type,
    }
    return ret

def process_candidate(candidate, race):
    """
    Process a single candidate into our intermediary format.
    """
    ret = {
        'candidate_id': _generate_candidate_id(candidate, race),
        'first_name': candidate.first_name,
        'last_name': candidate.last_name,
        'race_id': candidate.ap_race_number,
        'party': candidate.party,
        'incumbent': candidate.is_incumbent,
    }
    return ret

def write_update(ticket, path):
    """
    Write an update
    """
    updates = []

    for race in ticket.races:
        update = {
            'race_id': race.ap_race_number,
            'precincts_reporting': 0,
            'precincts_total': 0,
            'candidates': [],
        }

        for ru in race.reporting_units:
            update['precincts_total'] += ru.precincts_total
            if ru.precincts_reporting:
                update['precincts_reporting'] += ru.precincts_reporting

        for candidate in race.candidates:
            update['candidates'].append({
                'candidate_id': _generate_candidate_id(candidate, race),
                'vote_count': candidate.vote_total
            })

        updates.append(update)

    with open(path, 'w') as f:
        json.dump(updates, f, indent=4)

def write_calls(ticket, path):
    """
    Write call data to disk
    """
    new_calls = []
    called_ids = []

    mod_string = ticket.client.ftp.sendcmd('MDTM %s' % ticket.results_file_path)
    mod_time = datetime.strptime(mod_string[4:], '%Y%m%d%H%M%S')

    if os.path.isfile(path):
        with open(path) as f:
            previous_calls = json.load(f)
            called_ids = [call.get('race_id') for call in previous_calls]
    else:
        previous_calls = []

    for race in ticket.races:
        if race.ap_race_number not in called_ids:
            winners = [_generate_candidate_id(candidate, race) for candidate in race.candidates if candidate.is_winner]
            runoff_winners = [_generate_candidate_id(candidate, race) for candidate in race.candidates if candidate.is_runoff]

            if len(runoff_winners):
                new_calls.append({
                    'race_id': race.ap_race_number,
                    'ap_runoff_winners': runoff_winners,
                    'ap_called_time': datetime.strftime(mod_time, '%Y-%m-%dT%H:%M:%SZ'),
                })

            if len(winners):
                new_calls.append({
                    'race_id': race.ap_race_number,
                    'ap_winner': winners[0],
                    'ap_called_time': datetime.strftime(mod_time, '%Y-%m-%dT%H:%M:%SZ'),
                })

    calls = previous_calls + new_calls

    with open(path, 'w') as f:
        json.dump(calls, f, indent=4)

@task
def clear_calls(path='data/calls.json'):
    """
    Clear calls json.
    """
    with open(path, 'w') as f:
        json.dump([], f)

@task
def record():
    """
    Begin recording AP data for playback later.
    """
    update_interval = 60 * 5 
    folder = datetime.now().strftime('%Y-%m-%d')
    root = 'data/recording/%s' % folder

    if os.path.exists(root):
        print 'ERROR: %s already exists. Delete it if you want to re-record for today!' % root
        return
    else:
        os.mkdir(root)

    while True:
        timestamp = time.time()
        folder = '%s/%s' % (root, timestamp)
        print "Writing to %s" % folder

        os.mkdir(folder)

        init(folder)
        update(folder)

        sleep(update_interval)

@task
def playback(folder_name='2014-10-06', update_interval=60):
    """
    Begin playback of recorded AP data.
    """
    from fabfile import data

    folder = 'data/recording/%s' % folder_name

    timestamps = sorted(os.listdir(folder))
    initial = '%s/%s' % (folder, timestamps[0])

    for timestamp in timestamps[1:]:
        print '==== LOADING NEXT DATA (%s) ====' % timestamp
        path = '%s/%s' % (folder, timestamp)
        data.load_updates('%s/update.json' % path)
        data.load_calls('%s/calls.json' % path)
        sleep(int(update_interval))

    print '==== PLAYBACK COMPLETE ===='
