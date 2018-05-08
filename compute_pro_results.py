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
import json
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

    # When necessary, we should get this number from an argument
    config.num_morning_times = 3

    # Load the PAX factors for later use.
    load_pax_factors(config)

    # Start with the actual work by reading the event results.
    event_results = read_event_results(config)
    # print('headers: ' + str(event_results['header']))
    # print('first row: ' + str(event_results['rows'][0]))

    # Find the first and last time columns.
    config.first_time_col, config.last_time_col = \
      find_time_col_range(event_results['header'])
    print('  times are in columns: %d - %d' %
          (config.first_time_col, config.last_time_col))

    # Only keep the valid rows.
    event_results['rows'] = \
      [row for row in event_results['rows'] if \
           has_valid_time(row, config)]
    print('  kept %d rows with valid times' % len(event_results['rows']))

    # For debugging, print out what we found.
    summarize_classes(event_results)

    pro_results = get_pro_results(event_results)
    summarize_classes(pro_results)
    print('Found %d pro entries.' % len(pro_results['rows']))

    print_times(pro_results, config)

    print('Will write pro results to:')
    print('  %s' % config.output_filename)


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


# If we never reach split_time_count (e.g., because it is None), we'll
# put the single best run in the first return value.
def identify_best_times(times, split_time_count):
    best_time_1_count = None
    best_time_2_count = None

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
                best_time_count = None
                best_time = None

    # Now record the best time. If we never got to the split, just
    # record this best time in the first spot and leave the second
    # as None.
    if not best_time_1_count:
        best_time_1_count = best_time_count
    else:
        best_time_2_count = best_time_count

    # Return the times.
    return best_time_1_count, best_time_2_count


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


def has_valid_time(row, config):
    times = get_times(row, config)
    return len(times) > 0


def get_times(row, config):
    times = []
    col = config.first_time_col
    while col < config.last_time_col and col < len(row):
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


def get_pax_time(time, class_name, config):
    pax_factor = config.pax_factors[class_name]
    return time * pax_factor


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


def print_times(results, config):
    class_col = find_class_column(results)
    for row in results['rows']:
        class_spec = row[class_col]
        class_name, _ = get_class_name_and_index(class_spec)
        print('%s %s (%s)' % (row[0], row[1], class_name))

        times = get_times(row, config)

        best_time_1, best_time_2 = \
          print_individual_times(times, class_name, config)

        final_time = best_time_1
        if best_time_2:
            final_time = final_time + best_time_2
        print('  combined:             %9.3f' % final_time)


def print_individual_times(times, class_name, config):
    best_time_1_count, best_time_2_count = \
      identify_best_times(times, config.num_morning_times)

    time_count = 0
    best_time_1 = None
    best_time_2 = None
    for _, penalty, raw_time in times:
        if raw_time:
            time_count = time_count + 1

            pax_time = get_pax_time(raw_time, class_name, config)

            flag_str = ' '
            if time_count == best_time_1_count or \
              time_count == best_time_2_count:
                flag_str = '*'
                if best_time_1:
                    best_time_2 = pax_time
                else:
                    best_time_1 = pax_time

            penalty_str = ''
            if penalty:
                if penalty.isdigit():
                    penalty_str = '(+' + penalty + ')'
                else:
                    penalty_str = penalty

            print('  %d:  %9.3f %-5s   %9.3f %s' %
                  (time_count, raw_time, penalty_str, pax_time, flag_str))
    return best_time_1, best_time_2


# ------------------------------------------------------------
# This is the magic that runs the main function when this is invoked
# as a script.

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
