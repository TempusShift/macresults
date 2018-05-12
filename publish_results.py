#!/usr/bin/env python3
#
# pylint: disable=missing-docstring
#
# This script reads the extracted results data and creates an HTML
# file with the results neatly formatted.
#
# Invoke this as:
# pylint: disable=line-too-long
#
# ./publish_results.py gen/mowog1-pro.json gen/mowog1-pro.html
#
# ./publish_results.py gen/mowog1-pro.json gen/mowog1-pro.html -n 'MOWOG 1 Pro Class' -d 'Saturday, 28 April, 2018' -l 'Canterbury Park'
#
# pylint: enable=line-too-long
#

import argparse
import base64
import sys

import pandas as pd

import pystache


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('results_filename',
                        help='The results file. Will extract results from ' +
                        'this file.')
    parser.add_argument('output_filename',
                        nargs='?',
                        help='The output file. Will write the HTML results ' +
                        'to this file.')
    parser.add_argument('-n',
                        dest='event_name',
                        default='',
                        help='The name of this event, e.g., ' +
                        '"MOWOG 1".')
    parser.add_argument('-d',
                        dest='event_date',
                        default='',
                        help='The date of this event, e.g., ' +
                        '"Saturday, 28 April, 2018".')
    parser.add_argument('-l',
                        dest='event_location',
                        default='',
                        help='The location of this event, e.g., '+
                        '"Canterbury Park, MN"')
    config = parser.parse_args(args)

    results = pd.read_json(config.results_filename,
                           orient='records', lines=True)
    print('Read results from: %s' % config.results_filename)
    # print(results.head())

    config.num_scored_times = determine_max_scored_times(results)
    print('  number of scored_runs:   %d' % config.num_scored_times)

    # Set up the templating.
    stache = pystache.Renderer(file_extension=False,
                               partials={})
    stache.partials['style'] = stache.load_template('templates/style.css')
    stache.partials['eventResult'] = \
      stache.load_template('templates/event-result.html')

    # Prepare the data do go in the template.
    # FIXME Need to populate most of this information dynamically.
    options = {
        'eventName': config.event_name,
        'date': config.event_date,
        'location': config.event_location,
        'numScoredTimes': config.num_scored_times,
        'numParticipants': len(results),
        'numRuns': results['num_runs'].sum(),
        'numDnfs': results['num_dnfs'].sum(),
        'numCones': results['num_cones'].sum()
    }

    # Print the information for the user to verify.
    for key, value in options.items():
        print('  %-25s%s' % (key + ':', value))

    options['logoDataUri'] = get_image_data_uri('templates/mac-logo-small.png')

    # Prepare class-specific stuff. Currently these are hard-coded to
    # Pro class. When we have multiple classes this needs to change.
    options['resultsClass'] = 'P'
    num_drivers = len(results)
    options['numDrivers'] = num_drivers
    # FIXME This computation needs to be 10% for N and there should be
    # no trophies for X.
    num_trophies = int(num_drivers * 0.2)
    options['numTrophies'] = num_trophies

    options['results'] = get_results_for_template(results, num_trophies, config)

    # Apply the template and write the result.
    event_results_template = \
      stache.load_template('templates/event-results.html')
    html = stache.render(event_results_template, options)
    if config.output_filename:
        print('Writing results to: %s' % config.output_filename)
        with open(config.output_filename, 'wt') as output_file:
            output_file.write(html)
    else:
        print(html)


# ------------------------------------------------------------
# Main functionality

def determine_max_scored_times(results):
    max_times = 0
    for times in results['times']:
        if len(times) > max_times:
            max_times = len(times)
    return max_times


def get_image_data_uri(filename):
    with open(filename, 'rb') as in_file:
        raw_data = in_file.read()
        base64_data = base64.b64encode(raw_data)
        data_uri = 'data:image/png;base64,' + base64_data.decode('utf-8')
        return data_uri


def get_results_for_template(results_df, num_trophies, config):
    sorted_results = results_df.sort_values(by=['final_time'])
    results = []
    rank = 0

    first_time = None
    prev_time = None
    for _, row in sorted_results.iterrows():
        result = {}

        rank = rank + 1
        result['rank'] = rank

        if rank <= num_trophies:
            result['trophy'] = 'T'

        result['cls'] = row['class_name']
        if row['class_index']:
            result['cls'] = row['class_index'] + '-' + result['cls']

        result['number'] = row['CarNumber']
        result['driver'] = '%s %s' % (row['FirstName'], row['LastName'])
        result['vehicle'] = row['Car']

        result['times'] = get_times_for_template(row, config)

        final_time = row['final_time']
        result['finalTime'] = format_time(final_time)
        if not first_time:
            result['diffFromFirst'] = '-'
            result['diffFromPrev'] = '-'
            first_time = final_time
        else:
            result['diffFromFirst'] = format_time(final_time - first_time)
            result['diffFromPrev'] = format_time(final_time - prev_time)
        prev_time = final_time

        results.append(result)

    return results


def get_times_for_template(row, config):
    # Initialize the times array so that we are sure to have a value
    # in each cell.
    times = [{} for _ in range(config.num_scored_times)]

    # Loop over the times, formatting the times.
    pax_times = row['pax_times']
    penalties = [penalty for _, penalty, _ in row['times']]
    best_time_nums = row['best_time_nums']

    for index, (pax_time, penalty) in enumerate(zip(pax_times, penalties)):
        time = {}
        time['time'] = format_time(pax_time, penalty)
        if index + 1 in best_time_nums:
            time['timeClass'] = 'best'
        times[index] = time

    return times


def format_time(time, penalty=None):
    if penalty == 'DNF':
        return 'DNF'

    formatted_time = '%0.3f' % time
    try:
        cones = int(penalty)
        if cones > 0:
            formatted_time = formatted_time + '&nbsp;(%d)' % cones
    except TypeError:
        pass
    return formatted_time


# ------------------------------------------------------------
# This is the magic that runs the main function when this is invoked
# as a script.

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
