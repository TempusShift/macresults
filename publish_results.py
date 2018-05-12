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
    style_template = stache.load_template('templates/style.css')
    stache.partials['style'] = style_template

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
        'numRuns': results['num_runs'].sum()
    }

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
