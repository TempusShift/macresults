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
# ./publish_results.py gen/mowog1.json gen/mowog1-pro.html
#
# ./publish_results.py gen/mowog1.json gen/mowog1-pro.html -n 'MOWOG 1 Pro Class' -d 'Saturday, 28 April, 2018' -l 'Canterbury Park'
#
# pylint: enable=line-too-long
#

import argparse
import base64
import sys

import pandas as pd

import pystache


INVALID_TIME = 9999.999


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
    stache.partials['classResult'] = \
      stache.load_template('templates/event-class-result.html')
    stache.partials['rawResult'] = \
      stache.load_template('templates/raw-result.html')
    stache.partials['paxResult'] = \
      stache.load_template('templates/pax-result.html')

    # Prepare the data do go in the template.
    options = {
        'eventName': config.event_name,
        'date': config.event_date,
        'location': config.event_location,
        'numScoredTimes': config.num_scored_times,
        'numParticipants': len(results),
        'numRuns': results['num_runs'].sum(),
        'numDnfs': results['num_dnfs'].sum(),
        'numCones': results['num_cones'].sum(),
        'numDirtyRuns': results['num_dirty_runs'].sum()
    }

    # Print the information for the user to verify.
    for key, value in options.items():
        print('  %-25s%s' % (key + ':', value))

    options['logoDataUri'] = get_image_data_uri('templates/mac-logo-small.png')

    # Prepare class results
    options['classes'] = prepare_all_class_results(results, config)
    verify_class_results_counts(options)

    options['rawTimes'] = prepare_all_best_times(results, 'best_raw_time')
    options['paxTimes'] = prepare_all_best_times(results, 'best_pax_time')

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


def prepare_all_class_results(results, config):
    classes = []

    # First accumulate the index classes.
    index_classes = [
        ('P', 'Pro'),
        ('Z', 'Pax Index'),
        ('C1', 'Combined 1'),
        ('C2', 'Combined 2'),
        ('Consolidated','Consolidated')
    ]
    for class_index, label in index_classes:
        selected_results = results.loc[results['class_index'] == class_index]
        # If we didn't have any drivers in this class, skip it.
        if selected_results.empty:
            continue
        class_results = \
          prepare_class_results(selected_results, \
                                class_index, label, 'PAX', config)
        classes.append(class_results)

    # Then accumulate the open classes. We split them by class_name
    # and sort them by pax_factor so that the fastest classes come
    # first. This gives a consistent ordering from event to event.
    open_results = results.loc[results['class_index'].isnull()]
    open_class_names = open_results['class_name'].unique()

    # Here we look at the pax_factors for the actual results so that
    # we don't need to load the factors into the config.
    open_class_names = sorted(open_class_names,
                              key=lambda x: get_pax_factor(open_results, x))

    for class_name in open_class_names:
        selected_results = \
          open_results.loc[open_results['class_name'] == class_name]
        class_results = \
          prepare_class_results(selected_results, \
                                class_name, 'Open', 'Raw', config)
        classes.append(class_results)

    return classes


def get_pax_factor(results, class_name):
    selected_results = \
      results.loc[results['class_name'] == class_name]
    return selected_results['pax_factor'].mean()


def prepare_class_results(results, class_name, label, time_type, config):
    class_results = {}

    # Prepare class-specific stuff.
    class_results['label'] = class_name
    if label:
        class_results['label'] = class_results['label'] + ' - ' + label
    num_drivers = len(results)
    class_results['numDrivers'] = num_drivers

    # Choose the trophy rate based on the class.
    trophy_rate = 0.2
    if class_name == 'N':
        trophy_rate = 0.1
    elif class_name == 'X':
        trophy_rate = 0.0
    num_trophies = int(round(num_drivers * trophy_rate))
    class_results['numTrophies'] = num_trophies

    class_results['timeType'] = time_type

    class_results['results'] = \
      get_results_for_template(results, num_trophies, time_type, config)

    return class_results


def get_results_for_template(results_df, num_trophies, time_type, config):
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

        result['times'] = get_times_for_template(row, time_type, config)

        final_time = row['final_time']
        result['finalTime'] = format_time(final_time)
        if not first_time:
            result['diffFromFirst'] = '-'
            result['diffFromPrev'] = '-'
            first_time = final_time
        elif final_time >= INVALID_TIME:
            result['diffFromFirst'] = '-'
            result['diffFromPrev'] = '-'
        else:
            result['diffFromFirst'] = format_time(final_time - first_time)
            result['diffFromPrev'] = format_time(final_time - prev_time)
        prev_time = final_time

        results.append(result)

    return results


def get_times_for_template(row, time_type, config):
    # Initialize the times array so that we are sure to have a value
    # in each cell.
    times = [{} for _ in range(config.num_scored_times)]

    # Loop over the times, formatting the times.
    scored_times = []
    if time_type == 'PAX':
        scored_times = row['pax_times']
    else:
        scored_times = [raw_time for _, _, raw_time in row['times']]
    penalties = [penalty for _, penalty, _ in row['times']]
    best_time_nums = row['best_time_nums']

    for index, (scored_time, penalty) in enumerate(zip(scored_times, penalties)):
        time = {}
        time['time'] = format_time(scored_time, penalty)
        if index + 1 in best_time_nums:
            time['timeClass'] = 'best'
        times[index] = time

    return times


def format_time(time, penalty=None):
    if penalty in ('DNF', 'OFF'):
        return penalty

    formatted_time = '%0.3f' % time
    try:
        cones = int(penalty)
        if cones > 0:
            formatted_time = formatted_time + '&nbsp;(%d)' % cones
    except TypeError:
        pass
    return formatted_time


def verify_class_results_counts(options):
    total_count = 0
    for class_results in options['classes']:
        class_count = len(class_results['results'])
        total_count = total_count + class_count
    if total_count != options['numParticipants']:
        print('WARNING: Class results cover %d participants, but we had results for %d.' %
              (total_count, options['numParticipants']))


def prepare_all_best_times(results_df, time_col_name):
    sorted_results = results_df.sort_values(by=[time_col_name])

    results = []
    rank = 0

    first_time = None
    prev_time = None
    for _, row in sorted_results.iterrows():
        result = {}

        rank = rank + 1
        result['rank'] = rank

        result['cls'] = row['class_name']
        if row['class_index']:
            result['cls'] = row['class_index'] + '-' + result['cls']

        result['number'] = row['CarNumber']
        result['driver'] = '%s %s' % (row['FirstName'], row['LastName'])
        result['vehicle'] = row['Car']

        final_time = prepare_best_times(row, time_col_name, result)
        if not first_time:
            result['diffFromFirst'] = '-'
            result['diffFromPrev'] = '-'
            first_time = final_time
        else:
            result['diffFromFirst'] = format_time(final_time - first_time)
            result['diffFromPrev'] = format_time(final_time - prev_time)

        if time_col_name == 'best_pax_time':
            doty_points = row['doty_points']
            result['dotyPoints'] = format_time(doty_points)

        if final_time >= INVALID_TIME:
            result['diffFromFirst'] = '-'
            result['diffFromPrev'] = '-'
            result['dotyPoints'] = '-'

        prev_time = final_time
        results.append(result)

    best_times = {}
    best_times['results'] = results
    return best_times


def prepare_best_times(row, time_col_name, result):
    raw_time = row['best_raw_time']
    result['rawTime'] = format_time(raw_time)
    pax_factor = row['pax_factor']
    result['paxFactor'] = format_time(pax_factor)
    pax_time = row['best_pax_time']
    result['paxTime'] = format_time(pax_time)

    final_time = row[time_col_name]
    return final_time


# ------------------------------------------------------------
# This is the magic that runs the main function when this is invoked
# as a script.

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
