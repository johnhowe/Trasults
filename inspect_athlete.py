#!/usr/bin/env python

import argparse
import re
import csv
import random
from io import StringIO
from tinydb import TinyDB
from tinydb import where
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime, timedelta
from statistics import median, StatisticsError

parser = argparse.ArgumentParser(description='Process DB file and filter data.')
parser.add_argument('--db', default='db.json', help='Path to the DB file')
parser.add_argument('--given_name', help='Filter by given name')
parser.add_argument('--surname', help='Filter by surname')
parser.add_argument('--name', help='Filter by given name OR surname')
parser.add_argument('--representing', help='Filter by representing')
parser.add_argument('--stage', help='Filter by stage')
parser.add_argument('--dd', help='Filter by exact difficulty')
parser.add_argument('--mindd', help='Filter by minimum difficulty')
parser.add_argument('--mintof', help='Filter by minimum Time of Flight')
parser.add_argument('--minhd', help='Filter by minimum HD')
parser.add_argument('--minscore', help='Filter by minimum total score')
parser.add_argument('--skills', help='Filter by number of skills')
parser.add_argument('--since', help='Filter since given date (format: YYYY-MM-DD)')
parser.add_argument('--before', help='Filter before given date (format: YYYY-MM-DD)')
parser.add_argument('--year', type=int, help='Filter by year (format: YYYY)')
parser.add_argument('--event', help='Filter by competition event title')
parser.add_argument('--level', help='Filter by competition level')
parser.add_argument('--female', action='store_true', help='Try filter female competition levels')
parser.add_argument('--male', action='store_true', help='Try filter male competition levels')
parser.add_argument('--sort_by_date', action='store_true', help='Sort output by date')
parser.add_argument('--sort_by_execution', action='store_true', help='Sort output by execution score')
parser.add_argument('--sort_by_dd', action='store_true', help='Sort output by difficulty score')
parser.add_argument('--sort_by_tof', action='store_true', help='Sort output by ToF score')
parser.add_argument('--ddtof', action='store_true', help='Show DD + ToF score')
parser.add_argument('--plot', action='store_true', help='Plot results')
parser.add_argument('--plotsingle', action='store_true', help='Plot results in a singe over-lapping chart')
parser.add_argument('--csv', action='store_true', help='CSV output')
parser.add_argument('--all_deductions', action='store_true', help='Summarise with ALL deductions (rather than medians)')
parser.add_argument('--no_judge_summary', action='store_true', help='Suppress the printing of the judges summary')
parser.add_argument('--no_colour', action='store_true', help='Suppress coloured output')
args = parser.parse_args()

blue = '#3498DB'
green = '#2ECC71'
orange = '#FFA500'
pink = '#FF1493'
red = '#FF0000'

def get_total_score(r):
    nelements = int(r['frame_nelements'])
    if nelements == 0:
        return 0
    if r['competition_discipline'] == 'DMT':
        try:
            dd = round(float(r['frame_difficultyt_g']), 1)
            penalty = float(r['frame_penaltyt'])
            landing = float(r['esigma_l'])
            s1 = [e for e in [r['e1_s1'], r['e2_s1'], r['e3_s1'], r['e4_s1'], r['e5_s1']] if e is not None]
            s2 = [e for e in [r['e1_s2'], r['e2_s2'], r['e3_s2'], r['e4_s2'], r['e5_s2']] if e is not None]
            medians = [2 * median(s) for s in [s1, s2] if len(s) > 0]
            deductions = sum([round(float(n), 1) for n in medians[:nelements]])
            if deductions == 0:
                sigmas = [r['e1_sigma'], r['e2_sigma'], r['e3_sigma'], r['e4_sigma'], r['e5_sigma']]
                if sum(sigmas) == 0:
                    return 0
                deductions = 2 * median([a for a in sigmas if a is not None and a < 10 and a > 0])
            execution = [0,18,20][nelements] - deductions - landing
            #print(nelements, dd, penalty, landing, s1, s2, medians, deductions, execution)
            return execution + dd - penalty
        except StatisticsError:
            return 0

    return float(r['frame_mark_ttt_g'])

def get_timestamp(result):
    return float(result['timestamp'][0])

def get_execution(result):
    return float(result['esigma_sigma'])

def get_dd(result):
    return float(result['frame_difficultyt_g'])

def get_tof(result):
    return float(result['t_sigma'])

def get_heatmap_color(value):
    color_index = 232 + int(value / 4)
    return f'\033[48;5;{color_index}m'

class bcolors:
    END = '\033[0m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

def colourise(values):
    colored_string = ""
    invalid = sum(values) == 0
    for value in values:
        if invalid:
            colored_string += "  "
            continue
        color = get_heatmap_color((10-value) * 5)
        if args.no_colour:
            colored_string += f"{value:2}"
        else:
            colored_string += f"{color}{value:2}{bcolors.END}"
    return colored_string

def red_if_nonzero(value):
    if value and not args.no_colour:
        return f"{bcolors.RED}{value:2}{bcolors.END}"
    return f"{value:2}"

def green_if_best(value, best):
    if float(value) == best and not args.no_colour:
        return f"{bcolors.GREEN}{value:6.3f}{bcolors.END}"
    return f"{value:6.3f}"

def green_if_true(text, is_true):
    if is_true and not args.no_colour:
        return f"{bcolors.GREEN}{text}{bcolors.END}"
    return f"{text}"

db = TinyDB(args.db)

if args.csv:
    csv_content = StringIO()
    csv_writer = csv.writer(csv_content, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    csv_prefix = [ "Date" ]
    csv_suffix = [ "Stage", "Event", "Competition", "Name", "Representing" ]
    csv_score = [ "DD", "ToF", "HD", "E", "L", "P", "Total", "Rank", "Elements", ]
    csv_writer.writerow(csv_prefix + csv_score + csv_suffix)

search_query = where('performance_discipline') == 'TRA'
search_query &= (~(where('competition_title').search("ZZ Test", flags=re.IGNORECASE))) \
    & (~(where('competition_title').search("ZZ DMT Test", flags=re.IGNORECASE))) \
    & (~(where('competition_title').search("zzTEST", flags=re.IGNORECASE)))

if args.surname:
    search_query &= where('person_surname').search(args.surname, flags=re.IGNORECASE)
if args.given_name:
    search_query &= where('person_given_name').search(args.given_name, flags=re.IGNORECASE)
if args.name:
    search_query &= (where('person_given_name').search(args.name, flags=re.IGNORECASE)) \
        | (where('person_surname').search(args.name, flags=re.IGNORECASE))
if args.representing:
    search_query &= where('person_representing').matches(args.representing, flags=re.IGNORECASE)
if args.mindd:
    search_query &= where('frame_difficultyt_g') >= float(args.mindd)
if args.mintof:
    search_query &= where('t_sigma') >= float(args.mintof)
if args.minhd:
    search_query &= where('h_sigma') >= float(args.minhd)
if args.minscore:
    search_query &= where('frame_mark_ttt_g') >= float(args.minscore)
if args.dd:
    search_query &= where('frame_difficultyt_g') == float(args.dd)
if args.stage:
    search_query &= where('stage_kind').matches(args.stage, flags=re.IGNORECASE)
if args.skills:
    search_query &= where('frame_nelements') == args.skills
if args.since:
    since_date = datetime.strptime(args.since, '%Y-%m-%d')
    since_timestamp = int(since_date.timestamp())
    search_query &= where('timestamp').any(lambda ts: ts >= since_timestamp)
if args.before:
    before_date = datetime.strptime(args.before, '%Y-%m-%d')
    before_timestamp = int(before_date.timestamp())
    search_query &= where('timestamp').any(lambda ts: ts <= before_timestamp)
if args.event:
    search_query &= where('event_title').search(args.event, flags=re.IGNORECASE)
if args.level:
    search_query &= where('competition_title').search(args.level, flags=re.IGNORECASE)
if args.female:
    search_query &= ((where('competition_title').search("fem", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("wom", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("gir", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("ladies", flags=re.IGNORECASE)) \
                     | (where('competition_title').search(r"\bf\)", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("flickor", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("女", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("Дев", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("Дев", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("Женщины", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("Юниорки", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("tytöt", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("dam", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("töt", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("naiset", flags=re.IGNORECASE)) \
                     | (where('competition_title').search("tüdrukud", flags=re.IGNORECASE)))
    search_query &= (~(where('competition_title').search(" men", flags=re.IGNORECASE))) \
        & (~(where('competition_title').search(" male", flags=re.IGNORECASE))) \
        & (~(where('competition_title').search("мужчины и женщины", flags=re.IGNORECASE))) \
        & (~(where('competition_title').search("&m", flags=re.IGNORECASE)))
if args.male:
    search_query &= ((~(where('competition_title').search("fem", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("wom", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("gir", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("ladies", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search(r" f\)", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("flickor", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("女", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("Дев", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("Дев", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("Женщины", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("Юниорки", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("tytöt", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("dam", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("töt", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("naiset", flags=re.IGNORECASE))) \
                    & (~(where('competition_title').search("tüdrukud", flags=re.IGNORECASE))))
if args.year:
    year_start = datetime(args.year, 1, 1)
    year_start_timestamp = int(year_start.timestamp())
    year_end = datetime(args.year, 12, 31)
    year_end_timestamp = int(year_end.timestamp())
    search_query &= where('timestamp').any(lambda ts: year_start_timestamp <= ts <= year_end_timestamp)

res = db.search(search_query)

if len(res) == 0:
    print("No matches")
    exit(0)

best = {}
best['total'] = 0
best['tof'] = 0
best['dd'] = 0
best['exec'] = 0
best['hd'] = 0
best['ddtof'] = 0
for r in res:
    best['total'] = max(best['total'], get_total_score(r))
    best['dd'] = max(best['dd'], float(r['frame_difficultyt_g']))
    best['tof'] = max(best['tof'], float(r['t_sigma']))
    best['hd'] = max(best['hd'], float(r['h_sigma']))
    #escore = 2*(int(r['frame_nelements']) - float(r['esigma_sigma'])) # TODO WHAT IS GOING ON HERE?
    escore = float(r['esigma_sigma'])
    best['exec'] = max(best['exec'], escore)
    ddtof = r['frame_difficultyt_g'] + r['t_sigma']
    best['ddtof'] = max(best['ddtof'], float(ddtof))


deduction_count = np.zeros((10,11))
xlabel = []
ylabel = []
for i in range(11):
    xlabel.append(str(i))
    ylabel.append(f"S{i+1}:")

if args.plot or args.plotsingle:
    e_data = []
    t_data = []
    h_data = []
    d_data = []
    s_data = []
    ts_data = []

sort_key = get_total_score
if args.sort_by_date:
    assert sort_key == get_total_score, "Can only use one sort key!"
    sort_key = get_timestamp
if args.sort_by_execution:
    assert sort_key == get_total_score, "Can only use one sort key!"
    sort_key = get_execution
if args.sort_by_dd:
    assert sort_key == get_total_score, "Can only use one sort key!"
    sort_key = get_dd
if args.sort_by_tof:
    assert sort_key == get_total_score, "Can only use one sort key!"
    sort_key = get_tof

sorted_res = sorted(res, key=sort_key)
competition_discipline = None
for i, r in enumerate(sorted_res):
    competition_discipline = r['competition_discipline']

    total_score = get_total_score(r)
    if total_score <= 0:
        continue # INVALID ROUTINE

    date_format = "%Y-%m-%d %H:%M:%S"
    start_time = datetime.strptime(r['frame_last_start_time_g'][:19], date_format)
    nelements = int(r['frame_nelements'])
    if nelements == 0:
        continue
    if r['frame_difficultyt_g'] > 30:
        continue
    if r['t_sigma'] > 25:
        continue

    if args.csv:
        csv_prefix = [ start_time.strftime('%Y-%m-%d') ]
        csv_suffix = [
            f"{r['stage_kind'][0]}{r['routine_number']}",
            r['event_title'],
            r['competition_title'],
            f"{r['person_given_name']} {r['person_surname']}",
            r['person_representing']
        ]
    else:
        prefix = f"{i+1:3d}: {start_time.strftime('%Y-%m-%d')} "
        if r['stage_kind'][0] == "Q":
            stage = f"Q{r['routine_number']}"
        elif r['stage_kind'] == "Semifinal":
            stage = "SF"
        elif r['stage_kind'] == "Final2":
            stage = "F2"
        elif r['stage_kind'] == "Final" or r['stage_kind'] == "Final1":
            stage = "F1"
        elif r['stage_kind'] == "Team Final":
            stage = f"TF"
        else:
            print(f"Staging error: {r['stage_kind']}")
            assert(False)
        suffix = f"{stage} {r['person_given_name']} {r['person_surname']} ({r['person_representing']}) {r['event_title']} - ({r['competition_title']}) "

    if r['competition_discipline'] == 'DMT':
        #execution = [int(n * 10) for n in [r['esigma_s1'], r['esigma_s2']][:nelements]]
        #landing = int(10*r['esigma_l'])
        #dd = round(float(r['frame_difficultyt_g']), 1)
        #total = round(float(r['frame_mark_ttt_g']), 1)
        #score = f"E:{execution} L:{landing} D:{dd} Total:{total}"

        if args.all_deductions:
            print("TODO")
            deductions = [int(n * 10) for n in [r['esigma_s1'], r['esigma_s2']][:int(r['frame_nelements'])]]
        else:
            deductions = [int(n * 10) for n in [r['esigma_s1'], r['esigma_s2']][:int(r['frame_nelements'])]]
        padding = "  " * (2 - int(r['frame_nelements']))
        escore = float(r['esigma_sigma'])
        #score = f"D:{r['frame_difficultyt_g']:4.1f} E:{escore:5.2f} {colourise(deductions)}{padding} L:{red_if_nonzero(landing)} P:{red_if_nonzero(penalty)} Total:{total_score} "

        rank = int(r['performance_rank_g'])
        penalty = int(10*float(r['frame_penaltyt']))
        landing = int(10*r['esigma_l'])
        exec_text = green_if_true(f"{escore:5.2f}", escore == best['exec'])
        dd_text = green_if_true(f"{r['frame_difficultyt_g']:4.1f}", r['frame_difficultyt_g'] == best['dd'])
        if args.csv:
            csv_score = [
                round(r['frame_difficultyt_g'], 1),
                0,
                0,
                round(escore, 1),
                round(landing, 1),
                round(penalty, 1),
                round(total_score, 2),
                round(rank, 0),
                round(nelements, 0)
            ]
        else:
            score = f"D:{dd_text} " + \
                f"E:{exec_text} {colourise(deductions)}{padding} " + \
                f"L:{red_if_nonzero(landing)} " + \
                f"P:{red_if_nonzero(penalty)} " + \
                f"Total:{green_if_best(total_score, best['total'])} "

    elif r['competition_discipline'] == 'TRA':
        landing = int(10*r['esigma_l'])
        ddtof = r['frame_difficultyt_g'] + r['t_sigma']
        if args.all_deductions:
            deductions = []

            for i in range(1, 7):
                key = f"e{i}_s"
                print(key)
                d = [r[f'e1_s1'] for j in range(1, 11)]
                #d = [int(r[key + str(j)]) * 10 for j in range(1, 11) if r[key + str(j)] is not None][:int(r['frame_nelements'])]
                print(d)
                deductions.append(d)
        else:
            deductions = [int(n * 10) for n in [r['esigma_s1'], r['esigma_s2'], r['esigma_s3'], r['esigma_s4'], r['esigma_s5'], r['esigma_s6'], r['esigma_s7'], r['esigma_s8'], r['esigma_s9'], r['esigma_s10']][:int(r['frame_nelements'])]]
        padding = "  " * (10 - nelements)
        escore = float(r['esigma_sigma'])
        dd_text = green_if_true(f"{r['frame_difficultyt_g']:4.1f}", r['frame_difficultyt_g'] == best['dd'])
        tof_text = green_if_true(f"{r['t_sigma']:5.2f}", r['t_sigma'] == best['tof'])
        ddtof_text = green_if_true(f"{ddtof:5.2f}", ddtof == best['ddtof'])
        hd_text = green_if_true(f"{r['h_sigma']:4.1f}", r['h_sigma'] == best['hd'])
        exec_text = green_if_true(f"{escore:5.2f}", escore == best['exec'])
        rank = int(r['performance_rank_g'])
        penalty = int(10*float(r['frame_penaltyt']))

        if args.csv:
            csv_score = [
                round(r['frame_difficultyt_g'], 1),
                round(r['t_sigma'], 2),
                round(r['h_sigma'], 1),
                round(escore, 1),
                round(landing, 1),
                round(penalty, 1),
                round(total_score, 2),
                round(rank, 0),
                round(nelements, 0)
            ]
        else:
            score = f"D:{dd_text} "
            score += f"T:{tof_text} "
            if args.ddtof: score += f"DT:{ddtof_text} "
            score += f"H:{hd_text} "
            score += f"E:{exec_text} {colourise(deductions)}{padding} "
            score += f"L:{red_if_nonzero(landing)} "
            score += f"Total:{green_if_best(total_score, best['total'])} "
            score += f"Rank:{rank:<2} "

    elif r['competition_discipline'] == 'SYN':
        deductions = [int(n * 10) for n in [r['esigma_s1'], r['esigma_s2'], r['esigma_s3'], r['esigma_s4'], r['esigma_s5'], r['esigma_s6'], r['esigma_s7'], r['esigma_s8'], r['esigma_s9'], r['esigma_s10']][:int(r['frame_nelements'])]]
        if args.csv:
            assert(False) # NOT IMPLEMENTED
        else:
            score = f"E:{deductions} H:{r['h_sigma']} D:{r['frame_difficultyt_g']} S:{r['t_sigma']} Total:{r['frame_mark_ttt_g']}"
    elif r['competition_discipline'] == 'TUM':
        if args.all_deductions:
            print("TODO")
        else:
            deductions = [int(n * 10) for n in [r['esigma_s1'], r['esigma_s2'], r['esigma_s3'], r['esigma_s4'], r['esigma_s5'], r['esigma_s6'], r['esigma_s7'], r['esigma_s8']][:int(r['frame_nelements'])]]
        padding = "  " * (2 - int(r['frame_nelements']))
        escore = float(r['esigma_sigma'])
        #score = f"D:{r['frame_difficultyt_g']:4.1f} E:{escore:5.2f} {colourise(deductions)}{padding} L:{red_if_nonzero(landing)} P:{red_if_nonzero(penalty)} Total:{total_score} "

        penalty = int(10*float(r['frame_penaltyt']))
        landing = int(10*r['esigma_l'])
        exec_text = green_if_true(f"{escore:5.2f}", escore == best['exec'])
        dd_text = green_if_true(f"{r['frame_difficultyt_g']:4.1f}", r['frame_difficultyt_g'] == best['dd'])
        if args.csv:
            score = f"{r['frame_difficultyt_g']:4.1f}, {escore:5.2f}, {landing}, {penalty}, {total_score}, {nelements}, "
        else:
            score = f"D:{dd_text} " + \
                f"E:{exec_text} {colourise(deductions)}{padding} " + \
                f"L:{red_if_nonzero(landing)} " + \
                f"P:{red_if_nonzero(penalty)} " + \
                f"Total:{green_if_best(total_score, best['total'])} "

    else:
        # Probably rhythmic or some other sport
        continue

    esum = sum([r[f'esigma_s{elem}'] for elem in range(1,nelements)])
    if esum:
        for elem in range(nelements):
            deduction = int(10 * r[f'esigma_s{elem+1}'])
            if deduction > 10:
                continue
            deduction_count[elem, deduction] += 1

    if args.csv:
        csv_writer.writerow(csv_prefix + csv_score + csv_suffix)

    else:
        print(prefix + score + suffix)

    if args.plot or args.plotsingle:
        if competition_discipline == 'TRA':
            e_data.append(2 * nelements - esum)
        elif competition_discipline == 'DMT':
            e_data.append(8 + nelements - esum/2)
        h_data.append(r['h_sigma'])
        d_data.append(r['frame_difficultyt_g'])
        t_data.append(r['t_sigma'])
        s_data.append(total_score)
        ts_data.append(float(r['timestamp'][0]))

if args.csv:
    csv_string = csv_content.getvalue()
    print(csv_string)
    args.no_judge_summary = True


if not args.no_judge_summary:
    total_row_sums = deduction_count.sum(axis=1)
    total_col_sums = deduction_count.sum(axis=0)

    deduction_output = []
    for r, row in enumerate(deduction_count):
        if total_row_sums[r] == 0:
            continue
        if args.no_colour:
            deduction_row = [f"{str(int(cell))}" for cell in row]
        else:
            deduction_row = [f"{get_heatmap_color(int(cell / total_row_sums[r] * 100))}{str(int(cell))}\033[0m" for cell in row]
        deduction_output.append('\t'.join([ylabel[r]] + deduction_row))
    total_row = [f"{str(int(cell))}" for cell in total_col_sums]
    deduction_output.append('\t'.join(['Total:'] + total_row))

    print()
    print("E:\t" + "\t".join(xlabel))
    print('\n'.join(deduction_output))

    colored_output = []
    for r, row in enumerate(deduction_count):
        if total_row_sums[r] == 0:
            continue
        if args.no_colour:
            colored_row = [f"{str(int(cell / total_row_sums[r] * 100))}" for cell in row]
        else:
            colored_row = [f"{get_heatmap_color(int(cell / total_row_sums[r] * 100))}{str(int(cell / total_row_sums[r] * 100))}%\033[0m" for cell in row]
        colored_output.append('\t'.join([ylabel[r]] + colored_row))

    total_percs = [f"{str(int(cell / sum(total_col_sums) * 1000)/10)}%" for cell in total_col_sums]
    colored_output.append('\t'.join(['Total:'] + total_percs))

    print()
    print("E:\t" + "\t".join(xlabel))
    print('\n'.join(colored_output))

if args.plot:
    dates = [datetime.fromtimestamp(ts) for ts in ts_data]
    fig, axs = plt.subplots(2, 2, figsize=(10, 8))
    ALPHA = 0.3
    SIZE = 3

    date_format = mdates.DateFormatter('%Y-%m-%d')

    date_data = mdates.date2num(dates)

    for ax in axs.flat:
        ax.tick_params(axis='x', rotation=45)

    colours = np.random.rand(len(s_data), 3)

    jitter = True
    if jitter:
        h_data = [x + random.uniform(-0.05, 0.05) for x in h_data]
        d_data = [x + random.uniform(-0.05, 0.05) for x in d_data]
        t_data = [x + random.uniform(-0.05, 0.05) for x in t_data]
        e_data = [x + random.uniform(-0.05, 0.05) for x in e_data]

    if competition_discipline == 'TRA':
        vert_range = 10.1

        # Plot HD component in the first subplot
        axs[0, 0].scatter(s_data, h_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=blue)
        coeffs_h = np.polyfit(s_data, h_data, 1)
        #trend_line_h = np.poly1d(coeffs_h)
        #axs[0, 0].plot(s_data, trend_line_h(s_data), linestyle='solid', linewidth=2, color=blue)
        min_vert = 0
        axs[0, 0].set_ylim(min_vert, min_vert + vert_range)
        axs[0, 0].set_title('HD')

        # Plot Difficulty component in the second subplot
        axs[0, 1].scatter(s_data, d_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=green)
        coeffs_d = np.polyfit(s_data, d_data, 1)
        #trend_line_d = np.poly1d(coeffs_d)
        #axs[0, 1].plot(s_data, trend_line_d(s_data), linestyle='solid', linewidth=2, color=green)
        min_vert = 8.5
        axs[0, 1].set_ylim(min_vert, min_vert + vert_range)
        axs[0, 1].set_title('Difficulty')

        # Plot ToF component in the third subplot
        axs[1, 0].scatter(s_data, t_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=red)
        coeffs_t = np.polyfit(s_data, t_data, 1)
        #trend_line_t = np.poly1d(coeffs_t)
        #axs[1, 0].plot(s_data, trend_line_t(s_data), linestyle='solid', linewidth=2, color=red)
        min_vert = 10
        axs[1, 0].set_ylim(min_vert, min_vert + vert_range)
        axs[1, 0].set_title('Time of Flight')

        # Plot Execution component in the fourth subplot
        axs[1, 1].scatter(s_data, e_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=orange)
        coeffs_e = np.polyfit(s_data, e_data, 1)
        #trend_line_e = np.poly1d(coeffs_e)
        #axs[1, 1].plot(s_data, trend_line_e(s_data), linestyle='solid', linewidth=2, color=orange)
        min_vert = 10
        axs[1, 1].set_ylim(min_vert, min_vert + vert_range)
        axs[1, 1].set_title('Execution')


#        axs[0, 0].scatter(s_data, h_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=blue)
#        coeffs_h = np.polyfit(s_data, h_data, 1)
#        trend_line_h = np.poly1d(coeffs_h)
#        axs[0, 0].xaxis.set_major_formatter(date_format)
#        #axs[0, 0].plot(s_data, trend_line_h(s_data), linestyle='solid', linewidth=2)
#        axs[0, 0].set_ylim(7, 10.1)
#        axs[0, 0].set_title('HD')
#
##        axs[0, 0].scatter(e_data, t_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=blue)
##        #coeffs_t = np.polyfit(d_data, t_data, 1)
##        #trend_line_t = np.poly1d(coeffs_t)
##        #axs[1, 0].xaxis.set_major_formatter(date_format)
##        #axs[1, 0].plot(s_data, trend_line_t(s_data), linestyle='solid', linewidth=2)
##        axs[0, 0].set_ylim(13, 17.1)
##        axs[0, 0].set_xlim(13, 17.1)
##        axs[0, 0].set_title('Time of Flight vs E')
#
#
#
#        axs[0, 1].scatter(s_data, d_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=green)
#        coeffs_d = np.polyfit(s_data, d_data, 1)
#        trend_line_d = np.poly1d(coeffs_d)
#        axs[0, 1].xaxis.set_major_formatter(date_format)
#        #axs[0, 1].plot(s_data, trend_line_d(s_data), linestyle='solid', linewidth=2)
#        #axs[0, 1].set_ylim(0, 20.1)
#        axs[0, 1].set_title('Difficulty')
#
##        axs[1, 0].scatter(d_data, t_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=red)
##        coeffs_t = np.polyfit(d_data, t_data, 1)
##        trend_line_t = np.poly1d(coeffs_t)
##        #axs[1, 0].xaxis.set_major_formatter(date_format)
##        #axs[1, 0].plot(s_data, trend_line_t(s_data), linestyle='solid', linewidth=2)
##        axs[1, 0].set_ylim(12, 18.1)
##        axs[1, 0].set_title('Time of Flight vs DD')
#
#        # Plot ToF component in the third subplot
#        axs[1, 0].scatter(s_data, t_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=red)
#        coeffs_t = np.polyfit(s_data, t_data, 1)
#        trend_line_t = np.poly1d(coeffs_t)
#        #axs[1, 0].xaxis.set_major_formatter(date_format)
#        #axs[1, 0].plot(s_data, trend_line_t(s_data), linestyle='solid', linewidth=2)
#        axs[1, 0].set_ylim(12, 18.1)
#        axs[1, 0].set_title('Time of Flight')
#
#
#        # Plot Execution component in the fourth subplot
#        axs[1, 1].scatter(s_data, e_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=orange)
#        coeffs_e = np.polyfit(s_data, e_data, 1)
#        trend_line_e = np.poly1d(coeffs_e)
#        #axs[1, 1].xaxis.set_major_formatter(date_format)
#        #axs[1, 1].plot(s_data, trend_line_e(s_data), linestyle='solid', linewidth=2)
#        #axs[1, 1].set_ylim(7, 20.1)
#        axs[1, 1].set_title('Execution')
    elif competition_discipline == 'DMT':
        # DD vs Total

        axs[0, 0].scatter(d_data, s_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=colours)
        coeffs_t = np.polyfit(d_data, s_data, 1)
        #trend_line_t = np.poly1d(coeffs_t)
        #axs[0, 0].xaxis.set_major_formatter(date_format)
        #axs[1, 0].plot(s_data, trend_line_t(s_data), linestyle='solid', linewidth=2)
        #axs[1, 0].set_ylim(12, 18.1)
        axs[0, 0].set_title('Difficulty vs Total')


        # Plot Difficulty
        axs[0, 1].scatter(s_data, d_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=colours)
        coeffs_d = np.polyfit(date_data, d_data, 1)
        #trend_line_d = np.poly1d(coeffs_d)
        axs[0, 1].xaxis.set_major_formatter(date_format)
        ##axs[0, 1].plot(s_data, trend_line_d(s_data), linestyle='solid', linewidth=2)
        #axs[0, 1].set_ylim(0, 20.1)
        axs[0, 1].set_title('Difficulty')

        # Plot ToF component in the third subplot
        axs[1, 0].scatter(d_data, e_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=colours)
        coeffs_t = np.polyfit(d_data, e_data, 1)
        #trend_line_t = np.poly1d(coeffs_t)
        #axs[1, 0].xaxis.set_major_formatter(date_format)
        #axs[1, 0].plot(s_data, trend_line_t(s_data), linestyle='solid', linewidth=2)
        #axs[1, 0].set_ylim(12, 18.1)
        axs[1, 0].set_title('Difficulty vs Execution')

        # # Plot ToF component in the third subplot
        # axs[1, 0].scatter(s_data, t_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=colours)
        # coeffs_t = np.polyfit(s_data, t_data, 1)
        # trend_line_t = np.poly1d(coeffs_t)
        # #axs[1, 0].xaxis.set_major_formatter(date_format)
        # #axs[1, 0].plot(s_data, trend_line_t(s_data), linestyle='solid', linewidth=2)
        # axs[1, 0].set_ylim(12, 18:.1)
        # axs[1, 0].set_title('Time of Flight')


        # Plot Execution component in the fourth subplot
        axs[1, 1].scatter(s_data, e_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=colours)
        coeffs_e = np.polyfit(s_data, e_data, 1)
        #trend_line_e = np.poly1d(coeffs_e)
        #axs[1, 1].xaxis.set_major_formatter(date_format)
        #axs[1, 1].plot(s_data, trend_line_e(s_data), linestyle='solid', linewidth=2)
        #axs[1, 1].set_ylim(7, 20.1)
        axs[1, 1].set_title('Execution')

    plt.tight_layout()

    plt.show()

elif args.plotsingle:
    dates = [datetime.fromtimestamp(ts) for ts in ts_data]
    fig, axs = plt.subplots(1, 1, figsize=(10, 8))
    ALPHA = 0.7
    SIZE = 30

    if competition_discipline == 'TRA':

        # Plot HD component
        axs.scatter(s_data, h_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=blue)
        coeffs_h = np.polyfit(s_data, h_data, 1)
        #trend_line_h = np.poly1d(coeffs_h)
        #axs.plot(s_data, trend_line_h(s_data), linestyle='solid', linewidth=2)
        #axs.set_ylim(8, 10.1)
        axs.set_title('HD')

        # Plot Difficulty component
        axs.scatter(s_data, d_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=green)
        coeffs_d = np.polyfit(s_data, d_data, 1)
        #trend_line_d = np.poly1d(coeffs_d)
        #axs.plot(s_data, trend_line_d(s_data), linestyle='solid', linewidth=2)
        #axs.set_ylim(8, 20.1)
        axs.set_title('Difficulty')

        # Plot ToF component
        axs.scatter(s_data, t_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=red)
        coeffs_t = np.polyfit(s_data, t_data, 1)
        #trend_line_t = np.poly1d(coeffs_t)
        #axs.plot(s_data, trend_line_t(s_data), linestyle='solid', linewidth=2)
        #axs.set_ylim(12, 20.1)
        axs.set_title('Time of Flight')

        # Plot Execution component
        axs.scatter(s_data, e_data, alpha=ALPHA, linewidths=0, marker='o', s=SIZE, color=orange)
        coeffs_e = np.polyfit(s_data, e_data, 1)
        #trend_line_e = np.poly1d(coeffs_e)
        #axs.plot(s_data, trend_line_e(s_data), linestyle='solid', linewidth=2)
        #axs.set_ylim(10, 20.1)
        axs.set_title('Execution')



    plt.tight_layout()

    plt.show()

