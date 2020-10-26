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

# Results Generation Commands

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

### 2018 MOWOG 6
```
./compute_results.py 2018/mowog6.csv gen/mowog6.json
./publish_event.py -n 'MOWOG 6' -d 'Saturday, 22 September, 2018' -l 'Dakota County Technical College' gen/mowog6.json 2018/mowog6-fin.html
```

### 2018 MOWOG 7
```
./compute_results.py 2018/mowog7.csv gen/mowog7.json
./publish_event.py -n 'MOWOG 7' -d 'Saturday, 13 October, 2018' -l 'Canterbury Park' gen/mowog7.json 2018/mowog7-fin.html
```

### 2018 MOWOG 8
```
./compute_results.py --no-pro-split 2018/mowog8.csv gen/mowog8.json
./publish_event.py -n 'MOWOG 8' -d 'Sunday, 14 October, 2018' -l 'Canterbury Park' gen/mowog8.json 2018/mowog8-fin.html
```

### 2018 MOWOG 9
```
./compute_results.py 2018/mowog9.csv gen/mowog9.json
./publish_event.py -n 'MOWOG 9' -d 'Saturday, 20 October, 2018' -l 'Canterbury Park' gen/mowog9.json 2018/mowog9-fin.html
```

### DOTY
```
./publish_doty.py -t 'MAC DOTY 2018' -n 9 -b 5 -o 2018/doty.html gen/mowog1.json gen/mowog2.json gen/mowog3.json gen/mowog4.json gen/mowog5.json gen/mowog6.json gen/mowog7.json gen/mowog8.json gen/mowog9.json
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

## 2019 Results

### 2019 MOWOG 1
```
./compute_results.py 2019/mowog1.csv gen/mowog1.json
./publish_event.py -n 'MOWOG 1' -d 'Saturday, 27 April, 2019' -l 'Canterbury Park' gen/mowog1.json 2019/mowog1-fin.html
```

### 2019 MOWOG 2
```
./compute_results.py 2019/mowog2.csv gen/mowog2.json
./publish_event.py -n 'MOWOG 2' -d 'Sunday, 28 April, 2019' -l 'Canterbury Park' gen/mowog2.json 2019/mowog2-fin.html
```

### 2019 MOWOG 3
```
./compute_results.py 2019/mowog3.csv gen/mowog3.json
./publish_event.py -n 'MOWOG 3' -d 'Saturday, 18 May, 2019' -l 'DCTC' gen/mowog3.json 2019/mowog3-fin.html
```

### 2019 MOWOG 4
```
./compute_results.py 2019/mowog4.csv gen/mowog4.json
./publish_event.py -n 'MOWOG 4' -d 'Saturday, 8 June, 2019' -l 'DCTC' gen/mowog4.json 2019/mowog4-fin.html
```

### 2019 MOWOG 5
```
./compute_results.py 2019/mowog5.csv gen/mowog5.json
./publish_event.py -n 'MOWOG 5' -d 'Saturday, 27 July, 2019' -l 'DCTC' gen/mowog5.json 2019/mowog5-fin.html
```

### 2019 MOWOG 6
```
./compute_results.py 2019/mowog6.csv gen/mowog6.json
./publish_event.py -n 'MOWOG 6' -d 'Sunday, 4 August, 2019' -l 'DCTC' gen/mowog6.json 2019/mowog6-fin.html
```

### 2019 MOWOG 7
```
./compute_results.py 2019/mowog7.csv gen/mowog7.json
./publish_event.py -n 'MOWOG 7' -d 'Sunday, 22 September, 2019' -l 'DCTC' gen/mowog7.json 2019/mowog7-fin.html
```

### 2019 MOWOG 8
```
./compute_results.py 2019/mowog8.csv gen/mowog8.json
./publish_event.py -n 'MOWOG 8' -d 'Saturday, 5 October, 2019' -l 'Canterbury Park' gen/mowog8.json 2019/mowog8-fin.html
```

### 2019 MOWOG 9
```
./compute_results.py 2019/mowog9.csv gen/mowog9.json
./publish_event.py -n 'MOWOG 9' -d 'Sunday, 6 October, 2019' -l 'Canterbury Park' gen/mowog9.json 2019/mowog9-fin.html
```

### DOTY
```
./publish_doty.py -t 'MAC DOTY 2019' -n 9 -b 5 -o 2019/doty.html gen/mowog1.json gen/mowog2.json gen/mowog3.json gen/mowog4.json gen/mowog5.json gen/mowog6.json gen/mowog7.json gen/mowog8.json gen/mowog9.json
```

### MOWOG Series
```
./publish_series.py -c 2019/mowog-series-conf.json
```

### Met Council Series
```
./publish_series.py -c 2019/mcas-series-conf.json
```

## 2020 Results

### 2020 MOWOG 1
```
./compute_results.py 2020/mowog1.csv gen/mowog1.json
./publish_event.py -n 'MOWOG 1' -d 'Saturday, 30 May, 2020' -l 'Canterbury Park' gen/mowog1.json 2020/mowog1-fin.html
```

### 2020 MOWOG 2
```
./compute_results.py 2020/mowog2.csv gen/mowog2.json
./publish_event.py -n 'MOWOG 2' -d 'Sunday, 31 May, 2020' -l 'Canterbury Park' gen/mowog2.json 2020/mowog2-fin.html
```

### 2020 MOWOG 3
```
./compute_results.py 2020/mowog3.csv gen/mowog3.json
./publish_event.py -n 'MOWOG 3' -d 'Sunday, 21 June, 2020' -l 'DCTC' gen/mowog3.json 2020/mowog3-fin.html
```

### 2020 MOWOG 4
```
./compute_results.py 2020/mowog4.csv gen/mowog4.json
./publish_event.py -n 'MOWOG 4' -d 'Sunday, 19 July, 2020' -l 'DCTC' gen/mowog4.json 2020/mowog4-fin.html
```

### 2020 MOWOG 5
```
./compute_results.py 2020/mowog5.csv gen/mowog5.json
./publish_event.py -n 'MOWOG 5' -d 'Sunday, 2 August, 2020' -l 'DCTC' gen/mowog5.json 2020/mowog5-fin.html
```

### 2020 MOWOG 6
```
./compute_results.py 2020/mowog6.csv gen/mowog6.json
./publish_event.py -n 'MOWOG 6' -d 'Saturday, 22 August, 2020' -l 'DCTC' gen/mowog6.json 2020/mowog6-fin.html
```

### 2020 MOWOG 7
```
./compute_results.py --no-pro-split 2020/mowog7.csv gen/mowog7.json
./publish_event.py -n 'MOWOG 7' -d 'Sunday, 13 September, 2020' -l 'BIR' gen/mowog7.json 2020/mowog7-fin.html
```

### 2020 MOWOG 8
```
./compute_results.py 2020/mowog8.csv gen/mowog8.json
./publish_event.py -n 'MOWOG 8' -d 'Sunday, 4 October, 2020' -l 'DCTC' gen/mowog8.json 2020/mowog8-fin.html
```

### 2020 MOWOG 9
Jay McKoskey was driving Felipe's STS car in the morning. But the engine failed
before afternoon runs. Jay finished the event in my ES car. Since he is in Pro,
we are giving him the ES PAX for the afternoon. My scripts don't handle this, so
I manually edited his times to yield the correct PAX times in the results.

ES PAX is 0.793 and STS PAX is 0.812. I made a trivial Excel sheet in the 2020
directory that walks through the calculations.

```
./compute_results.py -m 4 2020/mowog9.csv gen/mowog9.json
./publish_event.py -n 'MOWOG 9' -d 'Saturday, 10 October, 2020' -l 'Canterbury' gen/mowog9.json 2020/mowog9-fin.html
```

### 2020 MOWOG 10
```
./compute_results.py -m 4 2020/mowog10.csv gen/mowog10.json
./publish_event.py -n 'MOWOG 10' -d 'Sunday, 11 October, 2020' -l 'Canterbury' gen/mowog10.json 2020/mowog10-fin.html
```

### DOTY
```
./publish_doty.py -t 'MAC DOTY 2020' -n 10 -b 6 -o 2020/doty.html gen/mowog1.json gen/mowog2.json gen/mowog3.json gen/mowog4.json gen/mowog5.json gen/mowog6.json gen/mowog7.json gen/mowog8.json gen/mowog9.json gen/mowog10.json
```

### MOWOG Series
```
./publish_series.py -c 2020/mowog-series-conf.json
```

### Met Council Series
```
./publish_series.py -c 2020/mcas-series-conf.json
```

# Publishing
After generating results, use ftp to upload.
```sh
cd 2020
sftp -P 2222 mnautox@ftp.mnautox.com
> cd public_html/results/2020
> put mowog1-fin.html
> put doty.html
> put mowog-series.html
> put mcas-series.html
```

I used to ftp as shown below. But in mid-June 2020 I started getting a
fingerprint error. After logging into the HostGator customer portal I was able
to determine that ftp.mnautox.com works.
```sh
sftp -P 2222 mnautox@gator3066.hostgator.com
```
