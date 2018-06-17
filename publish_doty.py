#!/usr/bin/env python3
#
# pylint: disable=missing-docstring
#
# This scrip reads a series of event results files, computes the DOTY
# points, and creates an HTML file with the results neatly formatted.
#
# Invoke this as:
# ./publish_doty.py -t 'MAC DOTY 2018' -n 9 -o 2018/doty.html gen/mowog1.json gen/mowog2.json gen/mowog3.json
#

import argparse
import sys


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


# ------------------------------------------------------------
# This is the magic that runs the main function when this is invoked
# as a script.

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
