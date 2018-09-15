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

I wrote two scripts for this.

1. ```compute_results.py``` -- reads the event CSV and writes a JSON
   file with the complete results.
2. ```publish_event.py``` -- reads the event JSON and writes an HTML
   file with the full results.

We use templates for the output. Mustache
(https://mustache.github.io/) seems like a good syntax (certainly the
handlebarsjs version of JavaScript has been useful). The Python
library for mustache is pystache
(https://github.com/defunkt/pystache).

# Notes on Use
After generating results, use ftp to upload.
```
cd 2018
ftp --passive gator3066.hostgator.com
> cd public_html/results/2018
> put mowog1-fin.html
> put doty.html
> put mowog-series.html
> put mcas-series.html
```

## 2018 Results

### 2018 MOWOG 1
```
./compute_results.py 2018/mowog1.csv gen/mowog1.json
./publish_event.py -n 'MOWOG 1' -d 'Saturday, 28 April, 2018' -l 'Canterbury Park' gen/mowog1.json 2018/mowog1-fin.html
```

### 2018 MOWOG 2
```
./compute_results.py 2018/mowog2.csv gen/mowog2.json
./publish_event.py -n 'MOWOG 2' -d 'Sunday, 29 April, 2018' -l 'Canterbury Park' gen/mowog2.json 2018/mowog2-fin.html
```

### 2018 MOWOG 3
```
./compute_results.py 2018/mowog3.csv gen/mowog3.json
./publish_event.py -n 'MOWOG 3' -d 'Saturday, 9 June, 2018' -l 'Dakota County Technical College' gen/mowog3.json 2018/mowog3-fin.html
```

### 2018 MOWOG 4
```
./compute_results.py 2018/mowog4.csv gen/mowog4.json
./publish_event.py -n 'MOWOG 4' -d 'Sunday, 29 July, 2018' -l 'Dakota County Technical College' gen/mowog4.json 2018/mowog4-fin.html
```

### 2018 MOWOG 5
```
./compute_results.py 2018/mowog5.csv gen/mowog5.json
./publish_event.py -n 'MOWOG 5' -d 'Sunday, 12 August, 2018' -l 'Dakota County Technical College' gen/mowog5.json 2018/mowog5-fin.html
```

### DOTY
```
./publish_doty.py -t 'MAC 2018' -n 9 -b 5 -o 2018/doty.html gen/mowog1.json gen/mowog2.json gen/mowog3.json gen/mowog4.json gen/mowog5.json
```

### MOWOG Series
```
./publish_series.py -c 2018/mowog-series-conf.json
```

Or, deprecated all-args form:
```
./publish_series.py -t 'MOWOG 2018' -n 9 -b 5 -o 2018/mowog-series.html gen/mowog1.json gen/mowog2.json gen/mowog3.json gen/mowog4.json gen/mowog5.json
```

### Met Council Series
```
./publish_series.py -c 2018/mcas-series-conf.json
```

Or, deprecated all-args form:
```
./publish_series.py -t 'MCAS 2018' -n 7 -b 4 -o 2018/mcas-series.html gen/mowog2.json gen/cvscc.json 2018/com-mcas-points-20180715.xlsx gen/mowog4.json
```

### Other Clubs
```
./compute_results.py -m 4 2018/cvscc.csv gen/cvscc.json
./publish_event.py -n 'CVSCC Grand Prix at the Bridge' -d 'Sunday, 24 June, 2018' -l 'Chippewa Valley Technical College' gen/cvscc.json 2018/cvscc-fin.html
```
