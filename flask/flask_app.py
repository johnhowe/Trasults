#!/usr/bin/env python

import sys
import os
import sqlite3
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import (query_db, process_for_display, compute_stats, compute_form,
                compute_deduction_profile, get_leaderboard, get_competition_report)

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
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

        scatter_data = [
            {'x': r['dd'], 'y': r['total'],
             'label': f"{r['given_name']} {r['surname']}",
             'execution': r['execution']}
            for r in rows
        ]

        return render_template('results.html',
                               rows=rows, bests=bests,
                               discipline=discipline,
                               search_terms=search_terms_str,
                               scatter_data=scatter_data)

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
            sections[disc] = {
                'rows': processed,
                'bests': bests,
                'stats': compute_stats(processed),
                'form': compute_form(processed),
                'deduction_profile': compute_deduction_profile(processed),
            }
    return render_template('athlete.html',
                           given_name=given_name, surname=surname, sections=sections)


@app.route('/autocomplete/athletes')
def autocomplete_athletes():
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify([])
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT person_given_name, person_surname FROM routines
        WHERE frame_state='PUBLISHED'
          AND (person_given_name LIKE ? OR person_surname LIKE ?)
        LIMIT 20
    """, [f"%{q}%", f"%{q}%"])
    results = [{'given_name': r[0], 'surname': r[1]} for r in cursor.fetchall()]
    conn.close()
    return jsonify(results)


@app.route('/leaderboard')
def leaderboard():
    discipline = request.args.get('discipline', 'tra')
    year = request.args.get('year', '')
    representing = request.args.get('representing', '')
    rows = get_leaderboard(DB_PATH, discipline, year, representing)
    return render_template('leaderboard.html',
                           rows=rows, discipline=discipline,
                           year=year, representing=representing)


@app.route('/competition')
def competition():
    event = request.args.get('event', '')
    sections = []
    if event:
        raw = get_competition_report(DB_PATH, event)
        groups = defaultdict(list)
        for r in raw:
            key = (r['competition_discipline'], r['competition_title'], r['stage_kind'])
            groups[key].append(r)
        for (disc, title, stage), group_rows in sorted(groups.items()):
            processed, bests = process_for_display(group_rows)
            if processed:
                stage_lower = stage.lower()
                is_final = 'final' in stage_lower and 'team' not in stage_lower
                sections.append({
                    'disc': disc.lower(),
                    'title': title,
                    'stage': stage,
                    'rows': processed,
                    'bests': bests,
                    'is_final': is_final,
                })
    return render_template('competition.html', sections=sections, event=event)


@app.route('/compare')
def compare():
    a1_given = request.args.get('a1_given', '')
    a1_surname = request.args.get('a1_surname', '')
    a2_given = request.args.get('a2_given', '')
    a2_surname = request.args.get('a2_surname', '')
    discipline = request.args.get('discipline', 'tra')
    athletes = []
    for given, surname in [(a1_given, a1_surname), (a2_given, a2_surname)]:
        if given or surname:
            params = {'given_name': given, 'surname': surname, 'discipline': discipline}
            raw = query_db(DB_PATH, params, order_by='timestamp DESC')
            processed, bests = process_for_display(raw)
            athletes.append({
                'given_name': given,
                'surname': surname,
                'rows': processed,
                'bests': bests,
                'stats': compute_stats(processed) if processed else {},
                'form': compute_form(processed) if processed else {},
            })
    return render_template('compare.html', athletes=athletes, discipline=discipline,
                           a1_given=a1_given, a1_surname=a1_surname,
                           a2_given=a2_given, a2_surname=a2_surname)


@app.route('/clear', methods=['GET'])
def clear_session():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
