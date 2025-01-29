#!/usr/bin/env python

from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
import subprocess
import re

app = Flask(__name__)
app.secret_key = 'a88cf47e-ec3a-45e8-82e3-cdcb8afb699f'  # Replace with a strong secret key

# Converts ANSI colors to HTML
def ansi_to_html(text):
    ansi_escape = {
        r'\x1b\[30m': '<span style="color: black;">',
        r'\x1b\[31m': '<span style="color: red;">',
        r'\x1b\[32m': '<span style="color: green;">',
        r'\x1b\[33m': '<span style="color: yellow;">',
        r'\x1b\[34m': '<span style="color: blue;">',
        r'\x1b\[35m': '<span style="color: magenta;">',
        r'\x1b\[36m': '<span style="color: cyan;">',
        r'\x1b\[37m': '<span style="color: white;">',
        r'\x1b\[0m': '</span>',
        r'\x1b\[48;5;(\d+)m': lambda m: f'<span style="background-color: rgb({int(m.group(1))});">',
    }
    for ansi_code, html_tag in ansi_escape.items():
        text = re.sub(ansi_code, html_tag, text)
    text += '</span>'
    return text

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Store form data in session
        for field in [
            'given_name', 'surname', 'name', 'representing', 'stage',
            'dd', 'mindd', 'mintof', 'minhd', 'minscore',
            'skills', 'since', 'before', 'year', 'event', 'level' ]:
            session[field] = request.form.get(field)
            print(f"{field}: {session[field]}")

        # Store checkbox values in session
        session['female'] = 'female' in request.form
        session['male'] = 'male' in request.form
        session['sort_by_date'] = 'sort_by_date' in request.form
        session['sort_by_execution'] = 'sort_by_execution' in request.form
        session['sort_by_dd'] = 'sort_by_dd' in request.form
        session['sort_by_tof'] = 'sort_by_tof' in request.form

        # Prepare command options
        options = []
        search_terms = []

        discipline = request.form.get('discipline')
        options.append(f'--{discipline}')
        search_terms.append(discipline)
        session['discipline'] = discipline

        for field, flag in {
            'given_name': '--given_name',
            'surname': '--surname',
            'name': '--name',
            'representing': '--representing',
            'stage': '--stage',
            'dd': '--dd',
            'mindd': '--mindd',
            'mintof': '--mintof',
            'minhd': '--minhd',
            'minscore': '--minscore',
            'skills': '--skills',
            'since': '--since',
            'before': '--before',
            'year': '--year',
            'event': '--event',
            'level': '--level'
        }.items():
            if session[field]:
                options.append(flag)
                options.append(session[field])
                search_terms.append(f"{field}={session[field]}")

        if session.get('female'):
            options.append('--female')
            search_terms.append('female')
        if session.get('male'):
            options.append('--male')
            search_terms.append('male')
        if session.get('sort_by_date'):
            options.append('--sort_by_date')
        if session.get('sort_by_execution'):
            options.append('--sort_by_execution')
        if session.get('sort_by_dd'):
            options.append('--sort_by_dd')
        if session.get('sort_by_tof'):
            options.append('--sort_by_tof')

        command = ['python3', 'inspect_trasults.py'] + options
        print("$ ", command)
        result = subprocess.run(command, capture_output=True, text=True)
        output_html = ansi_to_html(result.stdout)
        search_terms_str = ', '.join(search_terms)
        print(f"search_terms_str = {search_terms_str}")
        return render_template('output.html', output=output_html, search_terms=search_terms_str)

    return render_template('index.html', **session)

@app.route('/clear', methods=['GET'])
def clear_session():
    session.clear()
    return redirect(url_for('index'))  # Redirect to the index page

if __name__ == '__main__':
    app.run(debug=True)
