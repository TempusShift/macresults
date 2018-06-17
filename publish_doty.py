#!/usr/bin/env python3
#
# pylint: disable=missing-docstring
#
# This scrip reads a series of event results files, computes the DOTY
# points, and creates an HTML file with the results neatly formatted.
#
# Invoke this as:
# pylint: disable=line-too-long
#
# ./publish_doty.py -t 'MAC DOTY 2018' -n 9 -b 5 -o 2018/doty.html gen/mowog1.json gen/mowog2.json gen/mowog3.json
#
# pylint: enable=line-too-long
#

import argparse
import base64
import math
import sys

import pandas as pd

import pystache


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('results_filenames',
                        nargs='+',
                        help='The results files. Will extract results from ' +
                        'these.')
    parser.add_argument('-o',
                        dest='output_filename',
                        help='The output file. Will write the HTML results ' +
                        'to this file.')
    parser.add_argument('-t',
                        dest='title',
                        default='MAC DOTY Results',
                        help='The title to put in the results file.')
    parser.add_argument('-n',
                        dest='num_events',
                        default=9,
                        type=int,
                        help='The number of events in the season.')
    parser.add_argument('-b',
                        dest='num_btp_events',
                        default=5,
                        type=int,
                        help='The number of events contributing to the ' +
                        'final DOTY score.')
    config = parser.parse_args(args)

    # Read the event results files.
    results = load_results(config)

    # Set up the templating.
    stache = pystache.Renderer(file_extension=False,
                               partials={})
    stache.partials['style'] = stache.load_template('templates/style.css')

    # Prepare the data do go in the template.
    options = {
        'title': config.title,
        'events': ['M%d' % event_num for event_num in range(1, config.num_events + 1)]
    }
    # print(options)
    options['results'] = prepare_results_for_template(results)
    options['logoDataUri'] = get_image_data_uri('templates/mac-logo-small.png')

    # Apply the template and write the result.
    doty_results_template = \
      stache.load_template('templates/doty-results.html')
    html = stache.render(doty_results_template, options)
    if config.output_filename:
        print('Writing DOTY results to: %s' % config.output_filename)
        with open(config.output_filename, 'wt') as output_file:
            output_file.write(html)
    else:
        print(html)


# ------------------------------------------------------------
# Helper functions

def load_results(config):
    results = pd.DataFrame(columns=['driver'])
    event_num = 1
    event_names = []
    for results_filename in config.results_filenames:
        event_name = 'M%d' % event_num
        event_names.append(event_name)
        print('Reading results for %s:' % event_name)
        print('  %s' % results_filename)

        event_results = pd.read_json(results_filename,
                                     orient='records', lines=True)
        event_results['driver'] = \
          event_results['FirstName'] + event_results['LastName']
        event_results[event_name] = event_results['doty_points']

        results = results.merge(event_results.loc[:, ['driver', event_name]],
                                on='driver',
                                how='outer')
        event_num = event_num + 1

    results['total_points'] = results[event_names].sum(axis=1)
    results['avg_points'] = results[event_names].mean(axis=1)
    results['num_events'] = results[event_names].count(axis=1)

    results = results.apply(add_btp_scores, axis=1, args=[event_names, config])

    print(results)
    return results


def add_btp_scores(row, event_names, config):
    actual_event_count = len(event_names)

    # Assume 100.0 points for each remaining event.
    num_remaining_events = config.num_events - actual_event_count
    if num_remaining_events > config.num_btp_events:
        num_remaining_events = config.num_btp_events
    best_remaining_score = 100.0 * num_remaining_events

    # Get the keeper scores.
    scores = [0.0 if math.isnan(score) else score for score in row[event_names]]
    scores = sorted(scores, reverse=True)

    num_scores_to_keep = config.num_btp_events - num_remaining_events
    kept_scores = scores[:num_scores_to_keep]

    kept_score = sum(kept_scores)

    # Record the result
    row['btp'] = kept_score + best_remaining_score
    return row


def prepare_results_for_template(results_df):
    sorted_results = results_df.sort_values(by=['total_points'],
                                            ascending=False)
    results = []
    rank = 0

    first_time = None
    prev_time = None
    for _, row in sorted_results.iterrows():
        result = {}
        rank = rank + 1
        result['rank'] = rank

        result['driver'] = row['driver']

        result['num_events'] = row['num_events']
        result['total_points'] = format_score(row['total_points'])
        result['avg_points'] = format_score(row['avg_points'])
        result['btp'] = format_score(row['btp'])

        results.append(result)

    return results


# FIXME This is duplicated with the publish_results.py script, we
# should put them in a common place.
def get_image_data_uri(filename):
    with open(filename, 'rb') as in_file:
        raw_data = in_file.read()
        base64_data = base64.b64encode(raw_data)
        data_uri = 'data:image/png;base64,' + base64_data.decode('utf-8')
        return data_uri


def format_score(score):
    formatted_score = '%0.3f' % score
    return formatted_score


# ------------------------------------------------------------
# This is the magic that runs the main function when this is invoked
# as a script.

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
