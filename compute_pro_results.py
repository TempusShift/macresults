#!/usr/bin/env python3
#
# pylint: disable=missing-docstring
#
# This script reads the event results, extracts the information for
# the drivers in the pro class, computes split scoring results, and
# writes a CSV file with the results.
#
# Invoke this as:
#
# ./compute_pro_results.py 2018/mowog1.csv 2018/mowog1-pro.csv
#

import argparse
import csv
import sys

def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('results_filename',
                        help='The input file. Will extract results from ' +
                        'this file.')
    parser.add_argument('output_filename',
                        help='The output file. Will write pro results to ' +
                        'this file.')
    config = parser.parse_args(args)

    event_results = read_event_results(config)
    # print('headers: ' + str(event_results['header']))
    # print('first row: ' + str(event_results['rows'][0]))

    # Find the first and last time columns.
    first_time_col, last_time_col = find_time_col_range(event_results['header'])
    print('  times are in columns: %d - %d' % (first_time_col, last_time_col))

    # Only keep the valid rows.
    event_results['rows'] = \
      [row for row in event_results['rows'] if \
           has_valid_time(row, first_time_col, last_time_col)]
    print('  kept %d rows with valid times' % len(event_results['rows']))

    # For debugging, print out what we found.
    summarize_classes(event_results)

    pro_results = get_pro_results(event_results)
    summarize_classes(pro_results)
    print('Found %d pro entries.' % len(pro_results['rows']))

    for row in pro_results['rows']:
        print('%s %s' % (row[0], row[1]))
        for _, penalty, raw_time in \
          get_times(row, first_time_col, last_time_col):
            if raw_time:
                penalty_str = ''
                if penalty:
                    if penalty.isdigit():
                        penalty_str = ' (' + penalty + ')'
                    else:
                        penalty_str = ' ' + penalty
                print('  %0.3f%s' % (raw_time, penalty_str))

    print('Will write pro results to:')
    print('  %s' % config.output_filename)


# ------------------------------------------------------------
# Main functionality

def read_event_results(config):
    print('Reading event results from:')
    print('  %s' % config.results_filename)
    with open(config.results_filename) as results_file:
        results_reader = csv.reader(results_file)
        header = next(results_reader)
        print('  results file has:  %d columns' % len(header))
        rows = [row for row in results_reader]
        print('               and:  %d rows' % len(rows))

        results = {}
        results['header'] = header
        results['rows'] = rows
        return results


def get_pro_results(event_results):
    pro_results = {}
    pro_results['header'] = event_results['header']

    # First, find the class column.
    class_col = find_class_column(event_results)

    # Make a list of the pro rows.
    pro_results['rows'] = \
      [row for row in event_results['rows'] if has_pro_index(row[class_col])]
    return pro_results


# ------------------------------------------------------------
# Low level helpers

def find_time_col_range(header):
    first_col = None
    last_col = None
    for col, name in enumerate(header):
        if name.startswith('Run '):
            if not first_col:
                first_col = col
            else:
                last_col = col
    return first_col, last_col


def has_valid_time(row, first_col, last_col):
    times = get_times(row, first_col, last_col)
    return len(times) > 0


def get_times(row, first_col, last_col):
    times = []
    col = first_col
    while col < last_col and col < len(row):
        scratch_time = row[col]
        col = col + 1
        penalty = row[col]
        col = col + 1

        # Start with the raw time.
        raw_time = float(scratch_time)

        # Handle penalties, add time for cones or nullify time for
        # DNFs and reruns.
        if penalty:
            if penalty.isdigit():
                # Has cones, add two seconds for each.
                raw_time = raw_time + 2.0 * int(penalty)
            elif penalty == 'DNF':
                # This is a valid run, but a useless time.
                raw_time = 9999.999
            elif penalty.startswith('RERUN'):
                # This is not a valid time.
                raw_time = None
            else:
                raise ValueError('Don\'t know penalty: "%s"' % str(penalty))
        if scratch_time:
            times.append((scratch_time, penalty, raw_time))

    return times


def has_pro_index(class_spec):
    class_name, index = get_class_name_and_index(class_spec)
    if index == 'P' and class_name:
        return True
    return False


def get_class_name_and_index(class_spec):
    class_parts = class_spec.split('-')
    if len(class_parts) == 1:
        return class_parts[0], None
    if len(class_parts) == 2:
        return  class_parts[1], class_parts[0]
    raise ValueError('Could not determine class for "%s"' % str(class_spec))


def find_class_column(results):
    header = results['header']
    for col_num, col_name in enumerate(header):
        if col_name == 'Class':
            return col_num


# ------------------------------------------------------------
# Summary/printing functions

def summarize_classes(results):
    # First, find the class column.
    class_col = find_class_column(results)
    # print('Classes are in column: %d' % class_col)

    # Then, count the number of drivers in each class.
    classes = {}
    for row in results['rows']:
        class_name = row[class_col]
        if class_name not in classes:
            classes[class_name] = 0
        classes[class_name] = classes[class_name] + 1

    # Finally, print this out.
    print(str(classes))


# ------------------------------------------------------------
# This is the magic that runs the main function when this is invoked
# as a script.

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
