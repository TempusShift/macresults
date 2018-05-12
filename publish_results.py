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

    stache = pystache.Renderer(file_extension=False,
                               partials={})
    stache.partials['style'] = stache.load_template('templates/style.css')
    stache.partials['eventResult'] = \
      stache.load_template('templates/event-result.html')

    logo_data_uri = get_image_data_uri('templates/mac-logo-small.png')

    results = pd.read_json(config.results_filename,
                           orient='records', lines=True)
    print(results.head())

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

    options['results'] = [
        {
        'trophy': '',
        'rank': 1,
        'cls': 'FM',
        'number': 1,
        'driver': 'Jason Hobbs',
        'vehicle': '1999 Novakar J9 Mojave',
        'times': [
            { 'time': 30.625 },
            { 'time': 30.318 },
            { 'time': 29.579 },
            { 'time': 34.180 },
            { 'time': 29.498,
              'timeClass': 'best' },
            { 'time': 29.514 }
        ],
        'finalTime': 27.020,
        'diffFromFirst': 0.0,
        'diffFromPrev': 0.0
    }]

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


# ------------------------------------------------------------
# This is the magic that runs the main function when this is invoked
# as a script.

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
