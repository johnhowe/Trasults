#!/usr/bin/env python

from flask import Flask, render_template, request
import subprocess

app = Flask(__name__)

import re

def ansi_to_html(text):
    # Define a mapping of ANSI codes to HTML styles
    ansi_escape = {
        r'\x1b\[30m': '<span style="color: black;">',   # Black
        r'\x1b\[31m': '<span style="color: red;">',     # Red
        r'\x1b\[32m': '<span style="color: green;">',   # Green
        r'\x1b\[33m': '<span style="color: yellow;">',  # Yellow
        r'\x1b\[34m': '<span style="color: blue;">',    # Blue
        r'\x1b\[35m': '<span style="color: magenta;">', # Magenta
        r'\x1b\[36m': '<span style="color: cyan;">',    # Cyan
        r'\x1b\[37m': '<span style="color: white;">',   # White
        r'\x1b\[0m': '</span>',                          # Reset
        r'\x1b\[48;5;(\d+)m': lambda m: f'<span style="background-color: rgb({int(m.group(1))});">',  # Background color
    }

    # Replace ANSI codes with HTML
    for ansi_code, html_tag in ansi_escape.items():
        text = re.sub(ansi_code, html_tag, text)

    # Close any unclosed span tags
    text += '</span>'  # Ensure to close the last opened span
    return text

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        options = []
        search_terms = []

        # List of expected form fields and their corresponding flags
        form_fields = {
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
        }

        # Collect options for fields that have values
        for field, flag in form_fields.items():
            if request.form.get(field):
                options.append(flag)
                options.append(request.form[field])

        # Add flags that don't require values
        if request.form.get('female'):
            options.append('--female')
        if request.form.get('male'):
            options.append('--male')
        if request.form.get('sort_by_date'):
            options.append('--sort_by_date')
        if request.form.get('sort_by_execution'):
            options.append('--sort_by_execution')
        if request.form.get('sort_by_dd'):
            options.append('--sort_by_dd')
        if request.form.get('sort_by_tof'):
            options.append('--sort_by_tof')
        if request.form.get('ddtof'):
            options.append('--ddtof')
        if request.form.get('plot'):
            options.append('--plot')
        if request.form.get('plotsingle'):
            options.append('--plotsingle')
        if request.form.get('csv'):
            options.append('--csv')
        if request.form.get('all_deductions'):
            options.append('--all_deductions')
        if request.form.get('no_judge_summary'):
            options.append('--no_judge_summary')
        if request.form.get('no_colour'):
            options.append('--no_colour')

        # Call the script with the selected options
        db_mapping = {
            "tra": "tra_db2.json",  # Database for Trampoline
            "dmt": "dmt_db2.json",    # Database for Double Mini-Trampoline
            "tum": "tum_db2.json"     # Database for Tumbling
        }
        db_file = db_mapping.get(request.form.get('db'))
        command = ['python3', 'inspect_athlete.py', '--db', db_file, '--no_judge_summary'] + options
        print("Command to run:", command)  # Debugging line
        result = subprocess.run(command, capture_output=True, text=True)

        # Convert ANSI output to HTML
        output_html = ansi_to_html(result.stdout)

        # Join search terms into a single string
        search_terms_str = ', '.join(search_terms)

        # Render the output in a new template
        return render_template('output.html', output=output_html, search_terms=search_terms_str)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
