#!/usr/bin/env python3
#
# pylint: disable=missing-docstring
#
# This script reads a series of event results files, computes the DOTY
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
import json
import math
import sys

import numpy as np
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

    # Load the alias information.
    with open('aliases.json', 'rt', encoding='utf-8') as json_data:
        config.aliases = json.load(json_data)

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
    options['results'] = prepare_results_for_template(results, config)
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

        # FIXME This little bit of name fixing is duplicated from
        # publish_series.py.
        event_results['FirstName'].fillna('', inplace=True)
        event_results['LastName'].fillna('', inplace=True)
        event_results['driver'] = \
            event_results['FirstName'] + ' ' + event_results['LastName']
        event_results['driver'] = event_results['driver'].str.strip()

        # Make the names consistent.
        event_results['driver'] = \
            event_results['driver'].apply(dealias_name, args=[config.aliases])

        event_results[event_name] = event_results['doty_raw_points']

        results = results.merge(event_results.loc[:, ['driver', event_name]],
                                on='driver',
                                how='outer')
        event_num = event_num + 1

    # Compute the season points (and related summary values). These
    # are what we're really trying to get to.
    results = results.apply(add_season_points,
                            axis=1,
                            args=[event_names, config])

    # Compute the BTP points.
    results = results.apply(add_btp_scores, axis=1, args=[event_names, config])

    # print(results)
    return results


def add_season_points(row, event_names, config):
    # FIXME Write down exactly which events we are keeping, so that we
    # can highlight these in the results.

    # Decide how many of these scores to keep.
    num_actual_events = row[event_names].count()
    num_scores_to_keep = min(num_actual_events, config.num_btp_events)

    # Get the keeper scores.
    scores = zip([0.0 if math.isnan(score) else score for score in row[event_names]],
                 event_names)
    scores = sorted(scores, reverse=True, key=lambda x: x[0])
    kept_scores = scores[:num_scores_to_keep]

    # Record the season values.
    row['num_actual_events'] = num_actual_events
    row['num_kept_events'] = num_scores_to_keep
    row['total_points'] = sum([score for score, _event_name in kept_scores])
    row['avg_points'] = np.mean([score for score, _event_name in kept_scores])
    row['kept_events'] = set([event_name for _score, event_name in kept_scores])

    return row


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


# FIXME This is duplicated with the one in publish_series.py.
def dealias_name(name, aliases):
    lower_name = name.lower()
    if lower_name in aliases:
        return aliases[lower_name]
    return name


def prepare_results_for_template(results_df, config):
    sorted_results = results_df.sort_values(by=['total_points'],
                                            ascending=False)
    results = []
    rank = 0

    first_score = None
    prev_score = None
    for _, row in sorted_results.iterrows():
        result = {}
        rank = rank + 1
        result['rank'] = rank

        result['driver'] = row['driver']

        result['num_actual_events'] = row['num_actual_events']
        result['num_kept_events'] = row['num_kept_events']

        final_score = row['total_points']
        result['total_points'] = format_score(final_score)

        if not first_score:
            result['diffFromFirst'] = '-'
            result['diffFromPrev'] = '-'
            first_score = final_score
        else:
            result['diffFromFirst'] = format_score(final_score - first_score)
            result['diffFromPrev'] = format_score(final_score - prev_score)
        prev_score = final_score

        event_scores = []
        event_classes = []
        for event_num in range(1, config.num_events + 1):
            event_name = 'M%d' % event_num
            event_score = None
            try:
                event_score = row[event_name]
            except KeyError:
                # Didn't have any result for this array, use the
                # default value.
                pass
            event_scores.append({
                'score': format_score(event_score),
                'class': 'best' if event_name in row['kept_events'] else ''
            })
        result['event_scores'] = event_scores

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
    if score is None or math.isnan(score):
        formatted_score = '-'
    else:
        formatted_score = '%0.3f' % score
    return formatted_score


# ------------------------------------------------------------
# This is the magic that runs the main function when this is invoked
# as a script.

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
