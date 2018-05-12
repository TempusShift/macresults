# Process

1. Download results file.
   - <year>/event-name.csv
2. Fix any errors, ordering problems, etc.
3. Run script to prepare results. Needs to compute split score for pro
   class.
   - <year>/event-scores.csv
3. Run script to publish results.
   - <year>/event-fin.html
   - <year>/event-pax.html
   - <year>/event-raw.html
4. Run script to accumulate season scores.
   - Reads the event-scores files, prepares season-wide scores.

# Results Contents
We want to write the results as an html so that people can copy from
the table and past into Excel (or something). Also, this let's us make
the page have links to the specific classes.

## Per Event
### Divided by class
Trophy
Position
PAX class (if index applies)
 - Include factor?
Number
Driver
Car
Run 1-N
 - highlight best score(s)
 - include cones (or other) penalty
Total time (raw, indexed, split, per class)
Delta from first (in class)
Delta from next position
### Summary
Run counts:
 - Total
 - Clean
 - Dirty
   - With cones
     - Average cone count
     - Max cones
   - DNFs
   - Reruns
Driver counts:
 - Total
 - Clean
 - Dirty
   - With cones
   - With DNFs
   - With reruns

Should we also have these counts by class?

# Scoring Factors
## Class-specific Rules
 - Indexed-classes: Z, C1, C2
 - Raw-classes: N, open classes
 - Indexed and split: P
## What About Met Council Results?
 - I guess, prepare a CSV file for them?

# Implementation

Would be neat to write the scripts in Node/JavaScript so that they
could be ported to a web server or run on the timing machines. But,
for now anyway, Python is just much easier and more efficient for
development.

First: since we have the HTML results already, let's start by
extracting and preparing the pro information. We need that
urgently. We'll make two scripts for this:

1. ```compute_pro_results.py``` -- will read the event CSV and write
   out a CSV with the scores for the pro drivers.
2. ```publish_pro_standings.py``` -- will read the pro CSV and write
   an HTML file with these in them.

We want to use templates for the output. Mustache
(https://mustache.github.io/) seems like a good syntax (certainly the
handlebarsjs version of JavaScript has been useful). The Python
library for mustache is pystache
(https://github.com/defunkt/pystache).
