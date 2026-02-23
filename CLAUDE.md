# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TRASULTS is a trampoline competition results search and analysis tool. It queries a SQLite database of competition results and supports CLI and web-based interfaces. Disciplines supported: TRA (Trampoline), DMT (Double Mini-Trampoline), TUM (Tumbling).

## Running the Tools

```bash
# CLI search tool
python inspect_trasults.py --tra --given_name Dylan --since 2024-01-01
python inspect_trasults.py --dmt --surname Smith --country AUS

# Squad batch processor (iterates predefined athlete lists)
python inspect_squad.py

# Flask web app (from inside flask/ directory)
cd flask && flask run
# or
cd flask && python flask_app.py
```

## Architecture

### Data Flow
1. **CLI**: `inspect_trasults.py` builds parameterized SQL queries and prints colored terminal output
2. **Web**: `flask/flask_app.py` spawns `inspect_trasults.py` as a subprocess, captures ANSI output, converts to HTML, and renders it
3. **Batch**: `inspect_squad.py` defines squads as Python lists and iterates athletes → disciplines → calls inspect_trasults.py

### Key Modules

**`inspect_trasults.py`** (main logic)
- `build_query()` — constructs parameterized SQL WHERE clauses from CLI args
- `search_db()` — executes query against SQLite, returns list of dicts
- `print_results()` — formats output with ANSI colors and xterm-256 grayscale heatmaps for deductions

**`flask/flask_app.py`** (web wrapper)
- ANSI→HTML conversion: maps terminal color codes to `<span style="color:...">` tags; xterm-256 grayscale backgrounds use formula `v = 8 + 10*(index-232)` → `rgb(v,v,v)`
- Session state persists form values between requests

**`inspect_squad.py`** (batch analysis)
- Predefined squad lists: `national_squad`, `csg_team`, `wc_team`, `wagc_team`, `ice_team`, `worlds`, `olympicfinal`, `aus_itt`

### Database Schema (SQLite, `routines` table)
Key columns:
- Person: `person_given_name`, `person_surname`, `person_representing`
- Competition: `competition_discipline`, `competition_title`, `event_title`, `event_year`, `event_country`, `stage_kind`
- Scores: `frame_difficultyt_g`, `frame_mark_ttt_g`, `t_sigma`, `h_sigma`, `esigma_sigma`, `esigma_l`, `frame_penaltyt`, `performance_rank_g`
- Execution deductions: `esigma_s1`–`esigma_s10`, `e1_s1`, `e2_s1`, `e1_s2`, `e2_s2` (discipline-specific columns)
- State: `frame_state` (only `PUBLISHED` entries shown)

### Discipline-Specific Output Fields
- **TRA**: Difficulty, Time of Flight (`t_sigma`), Height (`h_sigma`), Execution (`esigma_sigma`), Landing (`esigma_l`), Penalty
- **DMT**: Difficulty, Execution, Landing, Penalty
- **TUM**: Difficulty, Execution, Landing, Penalty

### Gender Filtering
Gender is inferred from `competition_title` using regex (no dedicated gender column in DB).

## SQLite Database Files
Database `.sqlite` files are gitignored. The CLI tool expects a database path argument or a default location — check `inspect_trasults.py` for the `--db` argument or hardcoded default path.
