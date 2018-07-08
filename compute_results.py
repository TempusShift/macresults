#!/usr/bin/env python3
#
# pylint: disable=missing-docstring
#
# This script reads the event results, and prepares the data needed to
# generate results HTML files. Notably:
#  - Determines the scored runs (after reruns).
#    - Computing raw time after penalty
#  - Filters the results to just entries with scored runs.
#  - Augments rows with PAX factors.
#  - Computes PAX times.
#  - Identifies the best run (or runs for Pro class).
#  - Computes the final time (PAX or raw, combined when split
#    scoring).
#
# Invoke this as:
#
# ./compute_results.py 2018/mowog1.csv gen/mowog1.json
#

import argparse
import json
import math
import re
import sys

import pandas as pd


INVALID_TIME = 9999.999

RUN_COL_RE = re.compile(r'^run\s+(\d+)$', re.IGNORECASE)


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-m',
                        dest='num_morning_times',
                        default=3,
                        type=int,
                        help='The number of morning runs. Used for ' +
                        'computing pro split timing.')
    parser.add_argument('results_filename',
                        help='The input file. Will extract results from ' +
                        'this file.')
    parser.add_argument('output_filename',
                        nargs='?',
                        help='The output file. Will write results to ' +
                        'this file.')
    config = parser.parse_args(args)

    # Load the PAX factors for later use.
    load_pax_factors(config)

    # Start with the actual work by reading the event results.
    event_results = read_event_results(config)
    # print(event_results.describe())

    # Store these on the config because we might eventually get this
    # information from an external place (e.g., to support results
    # from other clubs).
    config.run_cols = identify_run_cols(event_results)
    print('Columns with runs in them:')
    print(config.run_cols)

    # Compute the scratch and raw times. Skips reruns and such.
    event_results = event_results.apply(add_scored_times, axis=1, args=[config])
    event_results = event_results.apply(add_run_stats, axis=1, args=[config])

    # Only keep rows with valid times. This prevents us from dealing
    # with rows for drivers who registered but did not show.
    event_results['has_valid_time'] = \
      event_results.apply(has_valid_time, axis=1)
    event_results = event_results.loc[event_results['has_valid_time']]
    print('  kept %d rows with valid times' % len(event_results))

    # Split up the index and classes.
    event_results = event_results.apply(add_class_names_and_indexes, axis=1)

    # Merge the PAX factors into the data.
    event_results = event_results.apply(add_pax_factors, axis=1, args=[config])

    # And add PAX times.
    event_results = event_results.apply(add_pax_times, axis=1)

    # Compute the best times. For indexed classes, these are PAX
    # times, otherwise these are raw. For the Pro class, we compute
    # both a morning and afternoon time.
    event_results = event_results.apply(add_best_times, axis=1, args=[config])
    event_results['doty_points'] = \
      event_results['best_pax_time'].min() / event_results['best_pax_time'] * 100.0

    # For debugging, print out what we found.
    # summarize_classes(event_results)

    if config.output_filename:
        write_results(event_results, config.output_filename)


# ------------------------------------------------------------
# Main functionality

def load_pax_factors(config):
    with open('pax-factors.json') as json_file:
        pax_data = json.load(json_file)

        print('PAX factors')
        config.pax_factors = {}
        for obj in pax_data:
            name = obj['name']
            factor = obj['factor']

            config.pax_factors[name] = factor
            print('  %10s => %0.3f' % (name, factor))


def read_event_results(config):
    print('Reading event results from:')
    print('  %s' % config.results_filename)
    results = pd.read_csv(config.results_filename)
    print(results.head())
    return results


def identify_run_cols(results):
    run_cols = []
    for col in results.columns:
        match = RUN_COL_RE.match(col)
        if match:
            pen_col = '%s Pen' % match.group(0)
            run_cols.append((col, pen_col))
    return run_cols


def add_scored_times(row, config):
    # print('row? ' + str(row))
    times = []

    # print('run_cols? ' + str(config.run_cols))
    for run_col, pen_col in config.run_cols:
        scratch_time = row[run_col]
        if not scratch_time or math.isnan(scratch_time):
            continue

        penalty = row[pen_col]
        # print('scratch: ' + str(scratch_time) + ' pen? ' + str(penalty))

        # Start with the scratch time.
        raw_time = scratch_time

        # Handle penalties, add time for cones or nullify time for
        # DNFs and reruns.
        if penalty:
            if isinstance(penalty, float) and math.isnan(penalty):
                # No penalty.
                penalty = int(0)

            if penalty == 'DNF':
                # This is a valid run, but a useless time.
                raw_time = INVALID_TIME
            elif str(penalty).startswith('RERUN'):
                # This is not a valid time.
                raw_time = None
            else:
                # Has cones, add two seconds for each.
                penalty = int(penalty)
                raw_time = raw_time + 2.0 * penalty

        if raw_time:
            times.append((scratch_time, penalty, raw_time))

    # print('times: ' + str(times))
    row['times'] = times
    return row


def has_valid_time(row):
    times = row['times']
    return len(times) > 0


def add_run_stats(row, config):
    num_runs = 0
    num_dnfs = 0
    num_reruns = 0
    num_cones = 0
    for run_col, pen_col in config.run_cols:
        scratch_time = row[run_col]
        if not scratch_time or math.isnan(scratch_time):
            continue

        num_runs = num_runs + 1

        penalty = row[pen_col]
        if penalty == 'DNF':
            num_dnfs = num_dnfs + 1
        elif str(penalty).startswith('RERUN'):
            num_reruns = num_reruns + 1
        else:
            try:
                cone_count = int(penalty)
                if cone_count > 0:
                    num_cones = num_cones + cone_count
            except ValueError:
                # We see this if penalty was NaN.
                pass

    row['num_runs'] = num_runs
    row['num_dnfs'] = num_dnfs
    row['num_reruns'] = num_reruns
    row['num_cones'] = num_cones
    return row

def add_class_names_and_indexes(row):
    class_spec = row['Class']
    class_name, class_index = get_class_name_and_index(class_spec)
    row['class_name'] = class_name
    row['class_index'] = class_index
    return row


def get_class_name_and_index(class_spec):
    class_parts = class_spec.split('-')
    if len(class_parts) == 1:
        return class_parts[0], None
    if len(class_parts) == 2:
        return  class_parts[1], class_parts[0]
    raise ValueError('Could not determine class for "%s"' % str(class_spec))


def add_pax_factors(row, config):
    class_name = row['class_name']
    pax_factor = config.pax_factors[class_name]
    row['pax_factor'] = pax_factor
    return row


def add_pax_times(row):
    pax_factor = row['pax_factor']
    times = row['times']

    pax_times = []
    for _, _, raw_time in times:
        pax_time = raw_time
        if raw_time and raw_time < INVALID_TIME:
            pax_time = raw_time * pax_factor

        pax_times.append(pax_time)

    row['pax_times'] = pax_times
    return row


def add_best_times(row, config):
    pax_factor = row['pax_factor']
    split = None
    if row['class_index'] == 'P':
        split = config.num_morning_times
    all_times = row['times']
    best_time_nums, best_times = identify_best_times(all_times, split)
    row['best_time_nums'] = best_time_nums

    final_time = INVALID_TIME
    best_raw_time = INVALID_TIME
    best_pax_time = INVALID_TIME
    if best_times:
        for time in best_times:
            if time < best_raw_time:
                best_raw_time = time
                best_pax_time = time * pax_factor

        # This is an indexed class, use PAX times.
        if row['class_index']:
            best_times = [time * pax_factor for time in best_times]

        # If this is the pro class and we only have one time, leave
        # the final time as INVALID.
        if row['class_index'] == 'P' and len(best_times) < 2:
            pass
        else:
            final_time = 0.0
            for time in best_times:
                final_time = final_time + time

    if final_time > INVALID_TIME:
        final_time = INVALID_TIME

    row['final_time'] = final_time
    row['best_raw_time'] = best_raw_time
    row['best_pax_time'] = best_pax_time
    return row


# If we never reach split_time_count (e.g., because it is None), we'll
# put the single best run in the first return value.
def identify_best_times(times, split_time_count):
    best_time_1_count = None
    best_time_1 = None
    best_time_2_count = None
    best_time_2 = None

    time_count = 0
    best_time_count = None
    best_time = None
    for _, _, raw_time in times:
        if raw_time:
            time_count = time_count + 1
            if not best_time_count or raw_time < best_time:
                best_time_count = time_count
                best_time = raw_time

            # If we're done with the morning, record it and reset to
            # find the next time.
            if time_count == split_time_count:
                best_time_1_count = best_time_count
                best_time_1 = best_time
                # Reset
                best_time_count = None
                best_time = None

    # Now record the best time. If we never got to the split, just
    # record this best time in the first spot and leave the second
    # as None.
    if not best_time_1_count:
        best_time_1_count = best_time_count
        best_time_1 = best_time
    else:
        best_time_2_count = best_time_count
        best_time_2 = best_time

    # Return the counts and times.
    best_counts = []
    best_times = []
    if best_time_1_count:
        best_counts.append(best_time_1_count)
        best_times.append(best_time_1)
        if best_time_2_count:
            best_counts.append(best_time_2_count)
            best_times.append(best_time_2)

    return best_counts, best_times


def write_results(results, output_filename):
    print('Will write results to:')
    print('  %s' % output_filename)
    json_string = results.to_json(orient='records', lines=True)
    with open(output_filename, 'wt') as out_file:
        out_file.write(json_string)


# ------------------------------------------------------------
# Summary/printing functions

def summarize_classes(results):
    # Then, count the number of drivers in each class.
    classes = {}
    for class_name in results['Class']:
        if class_name not in classes:
            classes[class_name] = 0
        classes[class_name] = classes[class_name] + 1

    # Finally, print this out.
    print(str(classes))


def print_times(row):
    full_class = '%s-' % row['class_index'] if row['class_index'] else ''
    full_class = full_class + row['class_name']
    print('%s %s (%s, %0.3f)' %
          (row['FirstName'], row['LastName'],
           full_class, row['pax_factor']))

    times = row['times']
    best_time_nums = row['best_time_nums']
    pax_times = row['pax_times']

    print_scored_times(times, best_time_nums, pax_times)

    final_time = row['final_time']
    print('  final time:           %9.3f' % final_time)


def print_scored_times(times, best_time_nums, pax_times):
    time_count = 0
    for (_, penalty, raw_time), pax_time in zip(times, pax_times):
        if raw_time:
            time_count = time_count + 1

            flag_str = ' '
            if time_count in best_time_nums:
                flag_str = '*'

            penalty_str = ''
            if penalty:
                if isinstance(penalty, int):
                    penalty_str = '(%d)' % penalty
                else:
                    penalty_str = penalty

            print('  %d:  %9.3f %-5s   %9.3f %s' %
                  (time_count, raw_time, penalty_str, pax_time, flag_str))


# ------------------------------------------------------------
# This is the magic that runs the main function when this is invoked
# as a script.

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
