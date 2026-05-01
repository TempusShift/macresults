#!/usr/bin/env python3
#
# Convert a MAC fin.html (publish_event.py output) to the AXti.me-style
# base HTML format (3-tab class/overall/PAX view with raw run times).
#
# The corresponding .json results file is auto-detected by replacing
# "-fin.html" with ".json" in the input filename.  You can also supply
# it explicitly with --json.
#
# Usage:
#   poetry run ./fin_to_base_html.py 2026/2026-mowog1-fin.html 2026/2026-mowog1.html
#   poetry run ./fin_to_base_html.py --json 2026/2026-mowog1.json \
#       2026/2026-mowog1-fin.html 2026/2026-mowog1-out.html

import argparse
import glob
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup


INVALID_TIME = 9999.999


# ---------------------------------------------------------------------------
# CLI

def main(args=None):
    parser = argparse.ArgumentParser(
        description='Convert a MAC fin.html to AXti.me-style base HTML.')
    parser.add_argument('fin_html',
                        help='Input fin.html file (publish_event.py output).')
    parser.add_argument('output_html',
                        help='Output .html file to write.')
    parser.add_argument('--json', dest='json_path',
                        help='JSONL results file. Auto-detected if omitted.')
    config = parser.parse_args(args)

    # Locate the JSONL file.
    if config.json_path:
        json_path = Path(config.json_path)
    else:
        fin_path = Path(config.fin_html)
        json_path = fin_path.parent / (fin_path.stem.replace('-fin', '') + '.json')
    if not json_path.exists():
        sys.exit(f'ERROR: JSONL file not found: {json_path}\n'
                 f'Provide it explicitly with --json.')

    # Load driver records.
    results = []
    with open(json_path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    print(f'Loaded {len(results)} results from {json_path}')

    # Parse event metadata from fin.html.
    with open(config.fin_html) as fh:
        soup = BeautifulSoup(fh.read(), 'html.parser')
    metadata = extract_metadata(soup)
    print(f'Event: {metadata.get("event_name")}  '
          f'Date: {metadata.get("date")}')

    # Produce the output HTML.
    html = generate_base_html(results, metadata)
    with open(config.output_html, 'w') as fh:
        fh.write(html)
    print(f'Written to {config.output_html}')


# ---------------------------------------------------------------------------
# Metadata extraction from fin.html

def extract_metadata(soup):
    meta = {}

    title_el = soup.find('title')
    if title_el:
        meta['title'] = title_el.get_text()

    event_name_el = soup.find('div', class_='event-name')
    if event_name_el:
        meta['event_name'] = (
            event_name_el.get_text(strip=True).replace(' Results', '').strip()
        )

    # Scan every leaf <div> inside event-details.
    event_details = soup.find('div', class_='event-details')
    date_found = False
    if event_details:
        for div in event_details.find_all('div'):
            if div.find('div'):          # skip non-leaf containers
                continue
            text = div.get_text(strip=True)
            if not text:
                continue
            lower = text.lower()
            if 'participants:' in lower:
                m = re.search(r'\d+', text)
                if m:
                    meta['participants'] = int(m.group())
            elif 'runs:' in lower:
                m = re.search(r'\d+', text)
                if m:
                    meta['runs'] = int(m.group())
            elif not date_found:
                meta['date'] = text
                date_found = True
            elif 'location' not in meta:
                meta['location'] = text

    # Fallback counts from results data (populated later if still absent).
    return meta


# ---------------------------------------------------------------------------
# HTML generation helpers

def fmt_time(raw_time, penalty=None, is_best=False):
    """Return a single <div class="time [best]">…</div> string."""
    cls = 'time best' if is_best else 'time'

    if penalty in ('DNF', 'OFF', 'DQ'):
        return f'<div class="{cls}"><span class="pen">{penalty}</span></div>'

    if raw_time is None or raw_time >= INVALID_TIME:
        return ''   # no time – skip

    if isinstance(penalty, str) and penalty.startswith('RERUN'):
        return f'<div class="{cls}">{raw_time:.3f} <span class="pen">RRN</span></div>'

    time_str = f'{raw_time:.3f}'
    try:
        cones = int(penalty) if penalty is not None else 0
        if cones > 0:
            time_str += f' <span class="pen">+{cones}</span>'
    except (TypeError, ValueError):
        # Unexpected penalty value – show it as-is.
        if penalty:
            time_str += f' <span class="pen">{penalty}</span>'

    return f'<div class="{cls}">{time_str}</div>'


def _best_run_index(driver):
    """
    Return the 0-based index of the single best run to highlight.
    For indexed classes use PAX times; for open classes use adjusted raw times.
    Returns -1 if no valid time exists.
    """
    if driver.get('class_index'):
        # Indexed class: best = lowest individual PAX time.
        pax = driver.get('pax_times', [])
        best_val, best_idx = INVALID_TIME, -1
        for i, t in enumerate(pax):
            if t < best_val:
                best_val, best_idx = t, i
        return best_idx
    else:
        # Open class: best = lowest adjusted raw time.
        times = driver.get('times', [])
        best_val, best_idx = INVALID_TIME, -1
        for i, (_, _, adj) in enumerate(times):
            if adj < best_val:
                best_val, best_idx = adj, i
        return best_idx


def run_times_html(driver):
    """Return all run time divs concatenated (plus clear-left footer)."""
    best_nums = set(driver.get('best_time_nums', []))
    parts = []
    scored_idx = 0
    run_num = 1
    while f'Run {run_num}' in driver:
        run_time = driver[f'Run {run_num}']
        penalty = driver.get(f'Run {run_num} Pen')
        run_num += 1
        if run_time is None:
            continue
        if isinstance(penalty, str) and penalty.startswith('RERUN'):
            div = fmt_time(run_time, penalty, False)
        else:
            scored_idx += 1
            is_best = scored_idx in best_nums
            div = fmt_time(run_time, penalty, is_best)
        if div:
            parts.append(div)
    parts.append('<div style="clear:left"></div>')
    return ''.join(parts)


def fmt_diff(delta):
    """Format a time difference with a leading '+' sign."""
    return f'+{delta:.3f}'


def safe_float(val, default=INVALID_TIME):
    """Convert val to float; return default for None or penalty strings."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# Class tab

def class_divider_key(driver):
    """Return the class-tab divider label for a driver."""
    idx = driver.get('class_index')
    return idx if idx else driver.get('class_name', driver.get('Class', 'X'))


def class_sort_key(driver):
    """Key used to sort drivers within a class group."""
    # Use final_time (PAX for indexed, raw for open) so ordering
    # matches what AXti.me would show.
    return driver.get('final_time', INVALID_TIME)


def best_display_time(driver):
    """
    Best 'score' to display in the class tab:
    - Best Indexed time (AXti.me-computed PAX) for indexed classes
    - Raw best time for open classes
    Using 'Best Indexed' / 'Best' from the CSV preserves the exact
    AXti.me-computed string values and avoids float rounding drift.
    """
    if driver.get('class_index'):
        val = driver.get('Best Indexed')
        if val:
            return safe_float(val, INVALID_TIME)
        return driver.get('best_pax_time', INVALID_TIME)
    val = driver.get('Best')
    if val:
        return safe_float(val, INVALID_TIME)
    return driver.get('best_raw_time', INVALID_TIME)


def generate_class_rows(results):
    """Generate <tr> rows for the class tab, grouped by divider label."""
    # Collect groups, preserving a stable order: indexed groups first
    # (P, Z, C1, C2, Consolidated), then open classes alphabetically.
    INDEX_ORDER = ['P', 'Z', 'C1', 'C2', 'Consolidated']

    groups = {}   # label → [driver, …]
    for d in results:
        key = class_divider_key(d)
        groups.setdefault(key, []).append(d)

    # Build ordered list of group labels.
    ordered_labels = [lbl for lbl in INDEX_ORDER if lbl in groups]
    open_labels = sorted(
        lbl for lbl in groups if lbl not in INDEX_ORDER
    )
    ordered_labels.extend(open_labels)

    rows = []
    for label in ordered_labels:
        drivers = sorted(groups[label], key=class_sort_key)

        rows.append(
            f'<tr class="divider"><td colspan="7">{label}</td></tr>'
        )

        first_time = None
        prev_time  = None
        for pos, drv in enumerate(drivers, start=1):
            score = best_display_time(drv)
            name  = (f'{drv["FirstName"]} {drv["LastName"]}'
                     f' #{drv["CarNumber"]}')
            car   = drv.get('Car', '')

            if first_time is None:
                d_first = '-'
                d_prev  = '-'
                first_time = score
            elif score >= INVALID_TIME:
                d_first = '-'
                d_prev  = '-'
            else:
                d_first = fmt_diff(score - first_time)
                d_prev  = fmt_diff(score - prev_time)
            prev_time = score

            times_html = run_times_html(drv)
            score_str  = f'{score:.3f}' if score < INVALID_TIME else 'DNF'

            rows.append(
                f'<tr class="row">'
                f'<td align="center">{pos}</td>'
                f'<td nowrap>{name}</td>'
                f'<td nowrap>{car}</td>'
                f'<td><strong>{score_str}</strong></td>'
                f'<td>{d_first}</td>'
                f'<td>{d_prev}</td>'
                f'<td>{times_html}</td>'
                f'</tr>'
            )

    return '\n'.join(rows)


# ---------------------------------------------------------------------------
# Overall tab (sorted by best raw time)

def generate_overall_rows(results):
    sorted_drivers = sorted(
        results,
        key=lambda d: d.get('best_raw_time',
                            safe_float(d.get('Best'), INVALID_TIME))
    )

    rows = []
    first_time = None
    prev_time  = None
    for rank, drv in enumerate(sorted_drivers, start=1):
        raw = drv.get('best_raw_time',
                      safe_float(drv.get('Best'), INVALID_TIME))
        name = (f'{drv["FirstName"]} {drv["LastName"]}'
                f' #{drv["CarNumber"]}')
        car  = drv.get('Car', '')
        cls  = drv.get('Class', '')

        if first_time is None:
            d_first = '-'
            d_prev  = '-'
            first_time = raw
        elif raw >= INVALID_TIME:
            d_first = '-'
            d_prev  = '-'
        else:
            d_first = fmt_diff(raw - first_time)
            d_prev  = fmt_diff(raw - prev_time)
        prev_time = raw

        times_html = run_times_html(drv)
        raw_str    = f'{raw:.3f}' if raw < INVALID_TIME else 'DNF'

        rows.append(
            f'<tr class="row">'
            f'<td>{rank}</td>'
            f'<td>{cls}'                    # intentionally no </td> – matches AXti.me quirk
            f'<td nowrap>{name}</td>'
            f'<td nowrap>{car}</td>'
            f'<td><strong>{raw_str}</strong></td>'
            f'<td>{d_first}</td>'
            f'<td>{d_prev}</td>'
            f'<td>{times_html}</td>'
            f'</tr>'
        )
    return '\n'.join(rows)


# ---------------------------------------------------------------------------
# PAX tab (sorted by best PAX time)

def generate_pax_rows(results):
    sorted_drivers = sorted(
        results,
        key=lambda d: d.get('best_pax_time', INVALID_TIME)
    )

    rows = []
    first_time = None
    prev_time  = None
    for rank, drv in enumerate(sorted_drivers, start=1):
        pax = drv.get('best_pax_time', INVALID_TIME)
        name = (f'{drv["FirstName"]} {drv["LastName"]}'
                f' #{drv["CarNumber"]}')
        car  = drv.get('Car', '')
        cls  = drv.get('Class', '')

        if first_time is None:
            d_first = '-'
            d_prev  = '-'
            first_time = pax
        elif pax >= INVALID_TIME:
            d_first = '-'
            d_prev  = '-'
        else:
            d_first = fmt_diff(pax - first_time)
            d_prev  = fmt_diff(pax - prev_time)
        prev_time = pax

        times_html = run_times_html(drv)
        pax_str    = f'{pax:.3f}' if pax < INVALID_TIME else 'DNF'

        rows.append(
            f'<tr class="row">'
            f'<td>{rank}</td>'
            f'<td>{cls}'                    # no </td> – AXti.me quirk
            f'<td nowrap>{name}</td>'
            f'<td nowrap>{car}</td>'
            f'<td><strong>{pax_str}</strong></td>'
            f'<td>{d_first}</td>'
            f'<td>{d_prev}</td>'
            f'<td>{times_html}</td>'
            f'</tr>'
        )
    return '\n'.join(rows)


# ---------------------------------------------------------------------------
# CSS extraction

def extract_css():
    """
    Borrow the inline CSS from the nearest existing base HTML in the repo.
    Searches the year directories newest-first.
    """
    for year in range(2030, 2017, -1):
        for path in glob.glob(f'{year}/*.html'):
            if '-fin' in path or 'series' in path or 'doty' in path:
                continue
            with open(path) as fh:
                content = fh.read()
            m = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
            if m:
                return m.group(1)
    return ''


# ---------------------------------------------------------------------------
# Top-level HTML assembly

def generate_base_html(results, metadata):
    event_name   = metadata.get('event_name', 'Event')
    date_str     = metadata.get('date', '')
    participants = metadata.get('participants', len(results))
    runs         = metadata.get('runs',
                                sum(d.get('num_runs', 0) for d in results))

    css           = extract_css()
    class_rows    = generate_class_rows(results)
    overall_rows  = generate_overall_rows(results)
    pax_rows      = generate_pax_rows(results)

    # Build as a single-line string (matching the AXti.me export style).
    return (
        f'<html><head><title>AXti.me Event Results:  {event_name}</title>'
        f'<style>{css}</style></head>'
        f'<body>'
        f'<div style="float:right;">Participants: {participants}<br/>Runs: {runs}</div>'
        f'<h1>Minnesota Autosports Club</h1>'
        f'<h2 style="margin-bottom:4px;">{event_name}</h2>'
        f'<h4 style="margin-top:0px;">{date_str}</h4>'
        f'<div class="clearfix"></div>'
        f'<p>'
        f'<button class="btn btn-large btn-info" onclick="showo()">Overall</button>'
        f'<button class="btn btn-large btn-success" onclick="showc()">Class</button>'
        f'<button class="btn btn-large btn-warning" onclick="showp()">PAX</button>'
        f'</p>'

        # Class tab (shown by default)
        f'<table id="result-class">'
        f'<thead>'
        f'<tr><th colspan="7">Class</th></tr>'
        f'<tr>'
        f'<th>Position</th><th>Driver</th><th>Car</th>'
        f'<th>Best</th><th>Diff.</th><th>Diff. Prev.</th><th>Raw Times</th>'
        f'</tr>'
        f'</thead>'
        f'<tbody>{class_rows}</tbody>'
        f'</table>'

        # Overall tab (hidden by default)
        f'<table id="result-overall" style="display:none;">'
        f'<thead>'
        f'<tr><th colspan="8">Overall</th></tr>'
        f'<tr>'
        f'<th>Rank</th><th>Class</th><th>Driver</th><th>Car</th>'
        f'<th>Best</th><th>Diff.</th><th>Diff. Prev.</th><th>Raw Times</th>'
        f'</tr>'
        f'</thead>'
        f'<tbody>{overall_rows}</tbody>'
        f'</table>'

        # PAX tab (hidden by default)
        f'<table id="result-pax" style="display:none;">'
        f'<thead>'
        f'<tr><th colspan="8">PAX</th></tr>'
        f'<tr>'
        f'<th>Rank</th><th>Class</th><th>Driver</th><th>Car</th>'
        f'<th>Best</th><th>Diff.</th><th>Diff. Prev.</th><th>Raw Times</th>'
        f'</tr>'
        f'</thead>'
        f'<tbody>{pax_rows}</tbody>'
        f'</table>'

        f'<div>Created by <a href="http://www.axti.me">AXti.me</a></div>'

        f'<script>'
        f'var c=document.getElementById("result-class");'
        f'var o=document.getElementById("result-overall");'
        f'var p=document.getElementById("result-pax");'
        f'function showc(){{c.style.display="";o.style.display="none";p.style.display="none";}}'
        f'function showo(){{c.style.display="none";o.style.display="";p.style.display="none";}}'
        f'function showp(){{c.style.display="none";o.style.display="none";p.style.display="";}}'
        f'</script>'
        f'</body></html>'
    )


if __name__ == '__main__':
    main()
