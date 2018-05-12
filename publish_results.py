#!/usr/bin/env python3
#
# pylint: disable=missing-docstring
#
# This script reads the extracted results data and creates an HTML
# file with the results neatly formatted.
#
# Invoke this as:
#
# ./publish_results.py gen/mowog1-pro.json gen/mowog1-pro.html
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
    config = parser.parse_args(args)

    results = pd.read_json(config.results_filename,
                           orient='records', lines=True)
    print(results.head())

    # FIXME We should dynamically determine this number from the data.
    config.max_times = 6

    # Set up the templating.
    stache = pystache.Renderer(file_extension=False,
                               partials={})
    stache.partials['style'] = stache.load_template('templates/style.css')
    stache.partials['eventResult'] = \
      stache.load_template('templates/event-result.html')

    logo_data_uri = get_image_data_uri('templates/mac-logo-small.png')

    # Prepare the data do go in the template.

    # FIXME Need to populate most of this information dynamically.
    options = {
        'logoDataUri': logo_data_uri,
        'eventName': 'MOWOG 1 Pro Class',
        'date': 'Saturday, 28 April 2018',
        'location': 'Canterbury Park',
        'numParticipants': len(results),
        'numRuns': results['num_runs'].sum(),
        'numDnfs': results['num_dnfs'].sum(),
        'numCones': results['num_cones'].sum()
    }

    options['results'] = get_results_for_template(results, config)

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

def get_image_data_uri(filename):
    with open(filename, 'rb') as in_file:
        raw_data = in_file.read()
        base64_data = base64.b64encode(raw_data)
        data_uri = 'data:image/png;base64,' + base64_data.decode('utf-8')
        return data_uri


def get_results_for_template(results_df, config):
    sorted_results = results_df.sort_values(by=['final_time'])
    results = []
    rank = 0

    first_time = None
    prev_time = None
    for _, row in sorted_results.iterrows():
        result = {}
        # FIXME Need trophy indicator.
        result['trophy'] = ''
        rank = rank + 1
        result['rank'] = rank

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
    times = [{} for _ in range(config.max_times)]

    # Loop over the times, formatting the times.
    pax_times = row['pax_times']
    best_time_nums = row['best_time_nums']

    for index, pax_time in enumerate(pax_times):
        time = {}
        # FIXME Add penalty information.
        time['time'] = format_time(pax_time)
        if index + 1 in best_time_nums:
            time['timeClass'] = 'best'
        times[index] = time

    return times


def format_time(time):
    return '%0.3f' % time


# ------------------------------------------------------------
# This is the magic that runs the main function when this is invoked
# as a script.

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
