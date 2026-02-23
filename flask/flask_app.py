#!/usr/bin/env python

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import query_db, process_for_display

from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session

app = Flask(__name__)
app.secret_key = 'a88cf47e-ec3a-45e8-82e3-cdcb8afb699f'

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'trasults.db')


def get_order_by(sess):
    if sess.get('sort_by_date'):
        return 'timestamp DESC'
    elif sess.get('sort_by_execution'):
        return 'esigma_sigma DESC'
    elif sess.get('sort_by_dd'):
        return 'frame_difficultyt_g DESC'
    elif sess.get('sort_by_tof'):
        return 't_sigma DESC'
    return 'frame_mark_ttt_g DESC'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        for field in [
            'given_name', 'surname', 'name', 'representing', 'stage', 'dd',
            'mindd', 'mintof', 'minhd', 'minscore', 'skills', 'since',
            'before', 'year', 'event', 'country', 'level']:
            session[field] = request.form.get(field)

        session['female'] = 'female' in request.form
        session['male'] = 'male' in request.form
        session['sort_by_date'] = 'sort_by_date' in request.form
        session['sort_by_execution'] = 'sort_by_execution' in request.form
        session['sort_by_dd'] = 'sort_by_dd' in request.form
        session['sort_by_tof'] = 'sort_by_tof' in request.form

        discipline = request.form.get('discipline')
        session['discipline'] = discipline

        search_terms = [discipline]
        for field in ['given_name', 'surname', 'name', 'representing', 'stage',
                      'dd', 'mindd', 'mintof', 'minhd', 'minscore', 'skills',
                      'since', 'before', 'year', 'event', 'country', 'level']:
            if session.get(field):
                search_terms.append(f"{field}={session[field]}")
        if session.get('female'):
            search_terms.append('female')
        if session.get('male'):
            search_terms.append('male')

        params = {
            'discipline': discipline,
            'given_name': session.get('given_name'),
            'surname': session.get('surname'),
            'name': session.get('name'),
            'representing': session.get('representing'),
            'stage': session.get('stage'),
            'dd': session.get('dd'),
            'mindd': session.get('mindd'),
            'mintof': session.get('mintof'),
            'minhd': session.get('minhd'),
            'minscore': session.get('minscore'),
            'skills': session.get('skills'),
            'since': session.get('since'),
            'before': session.get('before'),
            'year': session.get('year'),
            'event': session.get('event'),
            'country': session.get('country'),
            'level': session.get('level'),
            'female': session.get('female', False),
            'male': session.get('male', False),
        }

        raw = query_db(DB_PATH, params, get_order_by(session))
        rows, bests = process_for_display(raw)
        search_terms_str = ', '.join(search_terms)

        return render_template('results.html',
                               rows=rows, bests=bests,
                               discipline=discipline,
                               search_terms=search_terms_str)

    return render_template('index.html', **session)


@app.route('/athlete')
def athlete():
    given_name = request.args.get('given_name', '')
    surname = request.args.get('surname', '')
    sections = {}
    for disc in ['tra', 'dmt', 'tum']:
        params = {'given_name': given_name, 'surname': surname, 'discipline': disc}
        raw = query_db(DB_PATH, params, order_by='timestamp DESC')
        processed, bests = process_for_display(raw)
        if processed:
            sections[disc] = {'rows': processed, 'bests': bests}
    return render_template('athlete.html',
                           given_name=given_name, surname=surname, sections=sections)


@app.route('/clear', methods=['GET'])
def clear_session():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
