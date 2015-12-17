#!/usr/bin/env python

# This script takes a csv with two columns and tries to pair entries in the two
# columns together. It will match exact case-insensitive matches, then
# less exact matches (using Levenshtein algorith). Finally it will output what
# could not be matched. As items in the two lists are matched they are removed
# from the list.

# The output is a two column CSV written to STDOUT. The most confident matches
# are output first, least confident at the end. Unmatchable entries are last.

# usage: ./this_script.py < unmatched.csv > matched.csv

# This code is not terribly efficient and probably scales at O(n^2) where n is
# the number of rows. It could be made more efficient with a bit more caching.
# Probably would need to revisit the algorithm though.

# Code is also a bit disorganised and could be split up more cleanly. It worked
# for the intended purpose (matching LGA names in Nigeria) so development
# stopped.

import csv
import re
import sys
import fuzzy
dmeta = fuzzy.DMetaphone()

csv_reader = csv.reader(sys.stdin)
csv_writer = csv.writer(sys.stdout)

from_list = []
to_list   = []


for row in csv_reader:
    if row[0]: from_list.append( row[0] )
    if row[1]: to_list.append(   row[1] )

from_list.sort()
to_list.sort()


def split_words(words):
    """split ords on commas, dealing with whitespace"""
    space_clean = re.sub( '\s+',     ' ', words       )
    comma_clean = re.sub( '\s*,\s*', ',', space_clean )
    as_list     = re.split( ',', comma_clean )

    stripped = [ x.strip() for x in as_list ]

    return sorted( stripped )

def output(type, x, y):
    """output the results"""
    csv_writer.writerow( [ x, y ] )
    if x: from_list.remove(x)
    if y: to_list.remove(y)
    
def is_exact_match(x,y):
    """exact case insensitive match"""
    a,b = [ re.sub('\W+', ' ', v.lower()) for v in [ x,y ] ]
    return a.lower() == b.lower() or re.sub('\s', '', a) == re.sub('\s', '', b)
    
# from http://mwh.geek.nz/2009/04/26/python-damerau-levenshtein-distance/
def dameraulevenshtein(seq1, seq2):
    oneago = None
    thisrow = range(1, len(seq2) + 1) + [0]
    for x in xrange(len(seq1)):
        twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
        for y in xrange(len(seq2)):
            delcost = oneago[y] + 1
            addcost = thisrow[y - 1] + 1
            subcost = oneago[y - 1] + (seq1[x] != seq2[y])
            thisrow[y] = min(delcost, addcost, subcost)
            # This block deals with transpositions
            if (x > 0 and y > 0 and seq1[x] == seq2[y - 1]
                and seq1[x-1] == seq2[y] and seq1[x] != seq2[y]):
                thisrow[y] = min(thisrow[y], twoago[y - 2] + 1)
    return thisrow[len(seq2) - 1]


def best_levenshtein(x, y_list):

    if len(y_list) == 1:
        return y_list[0]

    lowest_score = 1000
    lowest_y = None

    for y in y_list:
        score = dameraulevenshtein(x.lower(),y.lower())
        # print "best_levenshtein trial: %s: %d" % (y, score)
        if score < lowest_score:
            lowest_score = score
            lowest_y = y

    # print 'best_levenshtein: %s -> %s, %s' % (x, lowest_y, str(y_list))
    return lowest_y

dmeta_match_cache = {}
def dmeta_match(a,b):
    key = "%s,%s" % (a,b)
    try:
        return dmeta_match_cache[key]
    except:
        # result = dameraulevenshtein(a,b)
        result = 100 - len( set(dmeta(a)) & set(dmeta(b)) )
        dmeta_match_cache[key] = result
        return result
    
def extract_best_match(matches):
    for match_count in range(1,100):
        for x in matches.keys():
            if len(matches[x]) == match_count:
                y = best_levenshtein(x, matches[x])
                return (match_count,x,y)
    return False

def match_pairs( list_one, list_two):

    # print list_one

    # print out the exact matches
    for x in list_one[:]:
        for y in list_two:
            if is_exact_match(x,y):
                output(0, x, y)
                continue

    # For some matching scenarios it is appropriate to match on whole words - for
    # example matching "John Smith" to "Smith, Mr J". The following code does that,
    # but is left commented out as it may not be the desired approach as it does not
    # deal well with slight mispellings.
    #
    # word_matches = defaultdict(list)
    # for x in list_one:
    #     for y in list_two:
    #         split_words = lambda word: re.split(r'\W+', word)
    #         match_count = len(set(split_words(x)) & set(split_words(y)))
    #         if match_count:
    #             word_matches[match_count].append((x,y))
    #             word_matches[(x,y)] = match_count
    #             word_matches[x].append(y)
    #             word_matches[y].append(x)
    #
    # for match_count in sorted( range(1,10), reverse=True):
    #     # print "---- %s ----" % match_count
    #     for x,y in word_matches[match_count]:
    #
    #         if x not in list_one or y not in list_two: continue
    #
    #         # generate all the pairings that we need to compare to
    #         pairings = []
    #         pairings += [ (x,matched_y) for matched_y in word_matches[x]]
    #         pairings += [ (matched_x,y) for matched_x in word_matches[y]]
    #         scores = [word_matches[pair] for pair in pairings if pair != (x,y)]
    #
    #         if len(scores) and max(scores) >= match_count: continue
    #
    #         del word_matches[x]
    #         del word_matches[y]
    #
    #         output(0, x, y)

    # print "# remaining list_one: %d, list_two: %d" % ( len(list_one), len(list_two) )

    # print out near matches as long as there are values remaining
    while len(list_one) or len(list_two):
        
        # setup variables to track best match
        lowest_score  = 100000
        dmeta_matches = {}
        
        # go through all pairings looking for best match using double metaphone
        for x in list_one:            
            x_matches = []
            dmeta_matches[x] = x_matches
            for y in list_two:
                score = dmeta_match(x,y)
                if score < lowest_score:
                    lowest_score = score
                    x_matches = []
                if score == lowest_score:
                    x_matches.append(y)
        
        # go through the equal dmeta matches and get the best levenshtein one
        best_match = extract_best_match(dmeta_matches)
        if best_match:
            (score,x,y) = best_match
            output(score, x, y )
            continue
    
        # setup variables to track best match
        lowest_score  = 100000
        dl_matches = {}

        # print '------------------'

        # go through all pairings looking for best match using double metaphone
        for x in list_one:            
            x_matches = []
            dl_matches[x] = x_matches
            for y in list_two:
                score = dameraulevenshtein(x,y)
                if score < lowest_score:
                    lowest_score = score
                    x_matches = []
                if score == lowest_score:
                    x_matches.append(y)

        # go through the equal dmeta matches and get the best levenshtein one
        best_match = extract_best_match(dl_matches)
        if best_match:
            (score,x,y) = best_match
            output(score, x, y )
            continue

        # no more good matches - print out unmatched remaining entries
        for x in list_one: output(100, x, '')
        for y in list_two: output(100, '', y)
        
    
        break
        
        
match_pairs(from_list, to_list)
