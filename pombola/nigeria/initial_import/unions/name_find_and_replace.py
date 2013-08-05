#!/usr/bin/env python


# Script that loads up a two col csv where the 1st col is the 'find' word and
# the secord is its replacement. Then reads STDIN and does the replacements
# before printing to STDOUT.

# Usage: cat input.txt | this_script replacements.csv > output.txt

import sys
import csv
import re

replacements = {}
for row in csv.reader( open(sys.argv[1]) ):
    if not (row[0] and row[1]): continue
    replacements[row[0]] = row[1]
    
# Try the replacements in order. Longest first. This should mean that a shorter
# replacement does not prevent a longer (more accurate) one from occurring.
replacement_trial_order = sorted( replacements.keys(), key=len, reverse=True )

# print replacement_trial_order

counter  = 0
for line in sys.stdin:
    counter += 1
    line = line.rstrip()
    for from_val in replacement_trial_order:
        line = re.sub( r'\b%s\b' % from_val, replacements[from_val], line)
    print line
