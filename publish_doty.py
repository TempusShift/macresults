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
# ./publish_doty.py -t 'MAC DOTY 2018' -n 9 -o 2018/doty.html gen/mowog1.json gen/mowog2.json gen/mowog3.json
#
# pylint: enable=line-too-long
#

import argparse
import base64
import sys

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
    config = parser.parse_args(args)

    # FIXME Read the event results files.

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

# FIXME This is duplicated with the publish_results.py script, we
# should put them in a common place.
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
