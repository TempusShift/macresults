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
# ./compute-pro-results.py 2018/mowog1.csv 2018/mowog1-pro.csv
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
    summarize_classes(event_results)

    pro_results = get_pro_results(event_results)
    summarize_classes(pro_results)
    print('Found %d pro entries.' % len(pro_results['rows']))

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


# ------------------------------------------------------------
# Low level helpers

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
    print('Classes are in column: %d' % class_col)

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
