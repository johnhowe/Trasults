#!/usr/bin/env python

import argparse
import sqlite3
from datetime import datetime
import csv
import sys
from statistics import median, StatisticsError

args = None

def build_query(args):
    query = "SELECT * FROM routines WHERE frame_state='PUBLISHED'"  # Start with a base query
    params = []

    if args.tra:
        query += " AND competition_discipline = 'TRA'"
    elif args.dmt:
        query += " AND competition_discipline = 'DMT'"
    elif args.syn:
        query += " AND competition_discipline = 'SYN'"
    elif args.tum:
        query += " AND competition_discipline = 'TUM'"
#    else: # By default, TRA
#        query += " AND competition_discipline = 'TRA'"

    if args.given_name:
        query += " AND person_given_name LIKE ?"
        params.append(f"%{args.given_name}%")
    if args.surname:
        query += " AND person_surname LIKE ?"
        params.append(f"%{args.surname}%")
    if args.name:
        query += " AND (person_given_name LIKE ? OR person_surname LIKE ?)"
        params.append(f"%{args.name}%")
        params.append(f"%{args.name}%")
    if args.representing:
        query += " AND person_representing LIKE ?"
        params.append(f"%{args.representing}%")
    if args.stage:
        query += " AND stage_kind LIKE ?"
        params.append(f"%{args.stage}%")
    if args.dd:
        query += " AND frame_difficultyt_g = ?"
        params.append(float(args.dd))
    if args.mindd:
        query += " AND frame_difficultyt_g >= ?"
        params.append(float(args.mindd))
    if args.mintof:
        query += " AND t_sigma >= ?"
        params.append(float(args.mintof))
    if args.minhd:
        query += " AND h_sigma >= ?"
        params.append(float(args.minhd))
    if args.minscore:
        query += " AND frame_mark_ttt_g >= ?"  ## TODO Tidy this up so that it is a recalculated score where necessary
        params.append(float(args.minscore))
    if args.skills:
        query += " AND frame_nelements = ?"
        params.append(args.skills)
    if args.since:
        since_date = datetime.strptime(args.since, '%Y-%m-%d')
        since_timestamp = int(since_date.timestamp())
        query += " AND timestamp >= ?"
        params.append(since_timestamp)
    if args.before:
        before_date = datetime.strptime(args.before, '%Y-%m-%d')
        before_timestamp = int(before_date.timestamp())
        query += " AND timestamp <= ?"
        params.append(before_timestamp)
    if args.country:
        query += " AND event_country LIKE ?"
        params.append(f"%{args.country}%")
    if args.year:
        query += " AND event_year = ?"
        params.append(args.year)
    if args.event:
        query += " AND event_title LIKE ?"
        params.append(f"%{args.event}%")
    if args.level:
        query += " AND competition_title LIKE ?"
        params.append(f"%{args.level}%")


    female_terms = [ "fem", "wom", "gir", "ladies", r"\bf\)", "flickor", "女",
        "Дев", "Женщины", "Юниорки", "tytöt", "dam", "töt", "naiset", "tüdrukud" ]
    not_female_terms = [ " men", " male", "мужчины", "мужчины и женщины", "&m" ]
    if args.female:
        female_conditions = " OR ".join([f"competition_title LIKE ?" for term in female_terms])
        not_female_conditions = " AND ".join([f"competition_title NOT LIKE ?" for term in not_female_terms])
        query += f" AND ({female_conditions})"
        params.extend([f"%{term}%" for term in female_terms])  # Add parameters for female terms
        query += f" AND ({not_female_conditions})"
        params.extend([f"%{term}%" for term in not_female_terms])  # Add parameters for not female terms

    if args.male:
        male_conditions = " AND ".join([f"competition_title NOT LIKE ?" for term in female_terms])
        query += f" AND ({male_conditions})"
        params.extend([f"%{term}%" for term in female_terms])  # Add parameters for female terms to exclude

    return query, params

def search_db():
    parser = argparse.ArgumentParser(description='Process DB file and filter data.')
    parser.add_argument('--db', default='trasults.db', help='Path to the DB file')
    parser.add_argument('--tra', action='store_true', help='Search for TRA routines')
    parser.add_argument('--dmt', action='store_true', help='Search for DMT routines')
    parser.add_argument('--syn', action='store_true', help='Search for SYN routines')
    parser.add_argument('--tum', action='store_true', help='Search for TUM routines')
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
    parser.add_argument('--country', help='Filter by competition host country')
    parser.add_argument('--event', help='Filter by competition event title')
    parser.add_argument('--level', help='Filter by competition level')
    parser.add_argument('--female', action='store_true', help='Try filter female competition levels')
    parser.add_argument('--male', action='store_true', help='Try filter male competition levels')
    parser.add_argument('--sort_by_date', action='store_true', help='Sort output by date')
    parser.add_argument('--sort_by_execution', action='store_true', help='Sort output by execution score')
    parser.add_argument('--sort_by_dd', action='store_true', help='Sort output by difficulty score')
    parser.add_argument('--sort_by_tof', action='store_true', help='Sort output by ToF score')
    parser.add_argument('--csv', action='store_true', help='CSV output')
    parser.add_argument('--all_deductions', action='store_true', help='Summarise with ALL deductions (rather than medians)')
    parser.add_argument('--no_judge_summary', action='store_true', help='Suppress the printing of the judges summary')
    parser.add_argument('--no_colour', action='store_true', help='Suppress coloured output')
    parser.add_argument('--invalid', action='store_true', help='Only show INVALID routines.')
    parser.add_argument('--nolimit', action='store_true', help='No limit on the number of routines (10,000)')

    global args
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()
    query, params = build_query(args)

    if args.sort_by_date:
        query += " ORDER BY timestamp DESC"
    elif args.sort_by_execution:
        query += " ORDER BY esigma_sigma DESC"
    elif args.sort_by_dd:
        query += " ORDER BY frame_difficultyt_g DESC"
    elif args.sort_by_tof:
        query += " ORDER BY t_sigma DESC"
    else:
        query += " ORDER BY frame_mark_ttt_g DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    results = [dict(zip(column_names, row)) for row in rows]
    conn.close()
    return results

def recalculate_dmt_execution_score(r):
    try:
        num_skills = int(r['frame_nelements'])
        s1 = [e for e in [r['e1_s1'], r['e2_s1'], r['e3_s1'], r['e4_s1'], r['e5_s1']] if e is not None]
        s2 = [e for e in [r['e1_s2'], r['e2_s2'], r['e3_s2'], r['e4_s2'], r['e5_s2']] if e is not None]
        medians = [2 * median(s) for s in [s1, s2] if len(s) > 0]
        deductions = sum([round(float(n), 1) for n in medians[:num_skills]])
        if deductions == 0:
            sigmas = [r['e1_sigma'], r['e2_sigma'], r['e3_sigma'], r['e4_sigma'], r['e5_sigma']]
            if sum(sigmas) == 0:
                return 0
            deductions = 2 * median([a for a in sigmas if a is not None and a < 10 and a > 0])
        execution = [0,18,20][num_skills] - deductions
        return execution
    except StatisticsError:
        return 0

def get_total_score(r):
    num_skills = int(r['frame_nelements'])
    if num_skills == 0:
        return 0
    if False and r['competition_discipline'] == 'DMT':
        try:
            dd = round(float(r['frame_difficultyt_g']), 1)
            penalty = float(r['frame_penaltyt'])
            execution = get_execution(r)
            #landing = float(r['esigma_l'])
            #print(num_skills, dd, penalty, landing, s1, s2, medians, deductions, execution)
            return execution + dd - penalty
        except StatisticsError:
            return 0
    return float(r['frame_mark_ttt_g'])

def get_timestamp(r):
    return float(r['timestamp'])

def get_execution(r):
    e = float(r['esigma_sigma'])
    if e > 1000: # Assuming it is entered in hundredths
        e = e / 100.0
    elif e > 100: # Assuming it is entered in tenths
        e = e / 10.0
    return e

    # if r['competition_discipline'] == 'DMT':
    #     return float(recalculate_dmt_execution_score(r))


def get_dd(r):
    return float(r['frame_difficultyt_g'])

def get_tof(r):
    return float(r['t_sigma'])

def get_hd(r):
    return float(r['h_sigma'])

def get_num_skills(r):
    return int(r['frame_nelements'])

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

def print_results(res):
    EDTH_MIN = 0
    E_MAX = 30
    D_MAX = 25
    T_MAX = 25
    H_MAX = 20
    TOTAL_MAX = E_MAX + D_MAX + T_MAX + H_MAX

    best = {
        'total': 0,
        'tof': 0,
        'dd': 0,
        'exec': 0,
        'hd': 0,
    }

    i = 0
    for r in res:
        timestamp = get_timestamp(r)
        total_score = get_total_score(r)
        execution = get_execution(r)
        dd = get_dd(r)
        tof = get_tof(r)
        hd = get_hd(r)
        num_skills = get_num_skills(r)

        if (("test" in str(r['person_given_name']).lower()) or
                ("test" in str(r['person_surname']).lower()) or
                ("test" in str(r['competition_title']).lower()) or
                ("test" in str(r['person_representing']).lower())):
            continue

        if (execution < EDTH_MIN or execution > E_MAX or
                dd < EDTH_MIN or dd > D_MAX or
                tof < EDTH_MIN or tof > T_MAX or
                total_score < EDTH_MIN or total_score > TOTAL_MAX or
                num_skills == 0):
            continue

        i=i+1
        if not args.nolimit and i  > 10000:
            break

        best['total'] = max(best['total'], total_score)
        best['dd'] = max(best['dd'], dd)
        best['tof'] = max(best['tof'], tof)
        best['hd'] = max(best['hd'], hd)
        best['exec'] = max(best['exec'], execution)

    i = 0
    invalid_routines = 0
    for r in res:
        is_invalid = False
        timestamp = get_timestamp(r)
        total_score = get_total_score(r)
        execution = get_execution(r)
        dd = get_dd(r)
        tof = get_tof(r)
        num_skills = get_num_skills(r)

        if (("test" in str(r['person_given_name']).lower()) or
                ("test" in str(r['person_surname']).lower()) or
                ("test" in str(r['competition_title']).lower()) or
                ("test" in str(r['person_representing']).lower())):
            continue

        if (execution < EDTH_MIN or execution > E_MAX or
                dd < EDTH_MIN or dd > D_MAX or
                tof < EDTH_MIN or tof > T_MAX or
                total_score < EDTH_MIN or total_score > TOTAL_MAX or
                num_skills == 0):
            invalid_routines += 1
            is_invalid = True

        if args.invalid and not is_invalid:
            continue
        if not args.invalid and is_invalid:
            continue

        i=i+1

        if not args.nolimit and i  > 10000:
            print("Limited to 10000 results!")
            break

        date_format = "%Y-%m-%d %H:%M:%S"
        start_time = datetime.strptime(r['frame_last_start_time_g'][:19], date_format)

        prefix = f"{i:3d}: {start_time.strftime('%Y-%m-%d')} "

        if r['stage_kind'][0] == "Q":
            stage = f"Q{int(r['routine_number'])}"
        elif r['stage_kind'] == "Semifinal":
            stage = "SF"
        elif r['stage_kind'] == "Final2":
            stage = "F2"
        elif r['stage_kind'] == "Final" or r['stage_kind'] == "Final1":
            stage = "F1"
        elif r['stage_kind'] == "Team Final":
            stage = f"TF"
        elif r['stage_kind'] == "Team Semifinal":
            stage = f"TS"
        else:
            print(f"Staging error: {r['stage_kind']}")
            assert(False)
        suffix = f"{stage} {r['person_given_name']} {r['person_surname']} ({r['person_representing']}) - {r['competition_title']} @ {r['event_title']} ({r['event_country']})"

        if r['competition_discipline'] == 'DMT':
            deductions = [int(n * 10) for n in [r['esigma_s1'], r['esigma_s2']][:int(r['frame_nelements'])]]
            padding = "  " * (2 - num_skills)
            escore = get_execution(r)
            #score = f"D:{r['frame_difficultyt_g']:4.1f} E:{escore:5.2f} {colourise(deductions)}{padding} L:{red_if_nonzero(landing)} P:{red_if_nonzero(penalty)} Total:{total_score} "

            #rank = int(r['performance_rank_g'])
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
                    #round(rank, 0),
                    round(num_skills, 0)
                ]
            else:
                score = f"Total:{green_if_best(total_score, best['total'])} " + \
                    f"D:{dd_text} " + \
                    f"E:{exec_text} {colourise(deductions)}{padding} " + \
                    f"L:{red_if_nonzero(landing)} " + \
                    f"P:{red_if_nonzero(penalty)} "


        elif r['competition_discipline'] == 'TRA':
            landing = int(10*r['esigma_l'])
            deductions = [int(n * 10) for n in [r['esigma_s1'], r['esigma_s2'], r['esigma_s3'], r['esigma_s4'], r['esigma_s5'], r['esigma_s6'], r['esigma_s7'], r['esigma_s8'], r['esigma_s9'], r['esigma_s10']][:int(r['frame_nelements'])]]
            padding = "  " * (10 - num_skills)
            escore = get_execution(r)
            dd_text = green_if_true(f"{r['frame_difficultyt_g']:4.1f}", r['frame_difficultyt_g'] == best['dd'])
            tof_text = green_if_true(f"{r['t_sigma']:5.2f}", r['t_sigma'] == best['tof'])
            hd_text = green_if_true(f"{r['h_sigma']:4.1f}", r['h_sigma'] == best['hd'])
            exec_text = green_if_true(f"{escore:5.2f}", escore == best['exec'])
            #rank = int(r['performance_rank_g'])
            penalty = int(10*float(r['frame_penaltyt']))
            score = f"Total:{green_if_best(total_score, best['total'])} "
            score += f"D:{dd_text} "
            score += f"T:{tof_text} "
            score += f"H:{hd_text} "
            score += f"E:{exec_text} {colourise(deductions)}{padding} "
            score += f"L:{red_if_nonzero(landing)} "
            #score += f"Rank:{rank:<2} "

        elif r['competition_discipline'] == 'SYN':
            score = " - SYNCHRO NOT YET IMPLEMENTED - "

        elif r['competition_discipline'] == 'TUM':
            deductions = [int(n * 10) for n in [r['esigma_s1'], r['esigma_s2'], r['esigma_s3'], r['esigma_s4'], r['esigma_s5'], r['esigma_s6'], r['esigma_s7'], r['esigma_s8']][:int(r['frame_nelements'])]]
            padding = "  " * (8 - num_skills)
            escore = get_execution(r)
            #score = f"D:{r['frame_difficultyt_g']:4.1f} E:{escore:5.2f} {colourise(deductions)}{padding} L:{red_if_nonzero(landing)} P:{red_if_nonzero(penalty)} Total:{total_score} "

            penalty = int(10*float(r['frame_penaltyt']))
            landing = int(10*r['esigma_l'])
            exec_text = green_if_true(f"{escore:5.2f}", escore == best['exec'])
            dd_text = green_if_true(f"{r['frame_difficultyt_g']:4.1f}", r['frame_difficultyt_g'] == best['dd'])
            if args.csv:
                score = f"{r['frame_difficultyt_g']:4.1f}, {escore:5.2f}, {landing}, {penalty}, {total_score}, {num_skills}, "
            else:
                score = f"Total:{green_if_best(total_score, best['total'])} " + \
                    f"D:{dd_text} " + \
                    f"E:{exec_text} {colourise(deductions)}{padding} " + \
                    f"L:{red_if_nonzero(landing)} " + \
                    f"P:{red_if_nonzero(penalty)} "

        else:
            # Probably rhythmic or some other sport
            continue

        print(f"{prefix} {score} {suffix}")

    if best['total']:
        print(f"\nBEST: Total:{best['total']} D:{best['dd']} T:{best['tof']} H:{best['hd']} E:{best['exec']}\n")
#    if invalid_routines > 0:
#        print(f"Skipped {invalid_routines} invalid routines.")

#    # Handle CSV output if specified
#    if args.csv:
#        csvwriter = csv.writer(sys.stdout)
#        csvwriter.writerow([description[0] for description in cursor.description])  # Write headers
#        csvwriter.writerows(results)
#    else:
#        # Print results to console
#        for row in results:
#            print(row)
#

def main():
    results = search_db()
    print_results(results)

if __name__ == "__main__":
    main()



