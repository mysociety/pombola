import sys
import re
import datetime

BLANK, SERIES_VOL_NO, TIME, DATE, START_TIME, \
HEADING, LINE, SCENE, SPEECH, ACTION = range(10)

SERIES_VOL_NO_PATTERN = r'^\s*([A-Z]+)\s+SERIES\s+VOL\.?\s*(\d+)\s*N(O|o|0)\.?\s*(\d+)\s*$'
DATE_PATTERN = r'^\s*(\w+\s*,\s*)?(\d+)\s+(\w+),?\s+(\d+)\s*$'

TITLES_TEMPLATE = '(Mr|Mrs|Ms|Alhaji|Madam|Dr|Prof)'
TIME_TEMPLATE = '(\d\d?)(:|\.)(\d\d)\s*(am|a.m|AM|A.M|pm|PM|p.m|P.M|noon)\.?[\s\-]*'


HEADING_PATTERN = r'^\s*([A-Z\s]+)\s*$'
SCENE_PATTERN = r'^\s*(\[[\w\s]+\])\s*$'
SPEECH_PATTERN = r'^\s*%s(.+):\s*(.*)\s*$' % TITLES_TEMPLATE
ACTION_PATTERN = r'^\s*%s(.+)\s*-\s+(.+)\s+-\s*$' % TITLES_TEMPLATE

START_TIME_PATTERN = r'The\s+House\s+met\s+at\s+%s' % TIME_TEMPLATE
TIME_PATTERN = r'^\s*%s$' % TIME_TEMPLATE


MONTHS = dict(jan=1, feb=2, mar=3, apr=4, may=5, jun=6, 
              jul=7, aug=8, sep=9, oct=10, nov=11, dec=12)

ORDINAL_WORDS = dict(first=1, second=2, third=3, fourth=4, fifth=5,
                     sixth=6, seventh=7)


HEADER_PATTERNS = (
    (DATE, DATE_PATTERN),
    (SERIES_VOL_NO, SERIES_VOL_NO_PATTERN)
    )

PATTERNS = (
    (SPEECH, SPEECH_PATTERN),
    (HEADING, HEADING_PATTERN),
    (TIME, TIME_PATTERN),
    (START_TIME, START_TIME_PATTERN),
    (SCENE, SCENE_PATTERN),
    (ACTION, ACTION_PATTERN)
    )


def parse_head(lines, nbr=0):

    series, vol, no, date = None, None, None, None
    
    for i, row in enumerate(lines):
        kind, line, match = row
        if SERIES_VOL_NO == kind:
            series = ORDINAL_WORDS[match.group(1).lower()]
            vol = int(match.group(2))
            no = int(match.group(4))
        elif DATE == kind:
            date = datetime.date(int(match.group(4)),
                                 MONTHS[match.group(3).lower()[:3]], 
                                 int(match.group(2)))
        if series and vol and no and date:
            nbr += i
            break
    return series, vol, no, date, nbr

def parse_body(lines):
    entries = []
    
    time = None
    topic = None
    page = None
    ahead = False

    kind, line, match = None, None, None

    # lines = (x for x in lines)
    while True:
        try:
            if not ahead:
                kind, line, match = lines.next()
            else:
                ahead = False

            if kind is SPEECH:
                speech, kind, line, match, ahead = parse_speech(time, match, lines)
                entries.append(speech)
            elif kind is HEADING:
                entries.append(dict(heading=line.strip(), time=time))
            elif kind in (TIME, START_TIME):
                time = parse_time(match)
            elif kind is ACTION:
                person = '%s%s' % (match.group(1), match.group(2))
                entries.append(dict(action=match.group(3), name=person.strip()))
            else:
                pass
        except StopIteration:
            break

    return entries


def body(lines):
    """Returns a generator for lines in the body of the hansard"""
    for i, row in enumerate(lines):
        _, line, _ = row
        if line.strip().startswith('Printed by Department of Official Report'):
            return (x for x in lines[i+1:])
    return (x for x in lines)


def parse_time(match):
    hh, mm = int(match.group(1)), int(match.group(3))
    t = match.group(4)
    if t in ('pm', 'PM', 'p.m', 'P.M') and hh != 12:
        hh += 12
    return datetime.time(hh, mm)

def parse_speech(time, match, lines):
    """A speech has the ff properties:
    1. Starts with a member's name followed by a colon
    2. Is followed by a number of LINEs or BLANKs"""
    name = '%s%s' % (match.group(1), match.group(2))
    speech = match.group(3)
    kind, line, match = None, None, None
    ahead = False

    while True:
        try:
            kind, line, match = lines.next()
            if kind == LINE: 
                speech += line
            elif kind == BLANK:
                speech = speech.strip() + '\n'
            else:
                ahead = True
                break
        except StopIteration:
            break
    return (dict(time=time, name=name, speech=speech.strip()), kind, line, match, ahead)

def parse_lines(lines, header=True):
    if header:
        return [parse_header_line(x) or parse_line(x) for x in lines]
    return [parse_line(x) for x in lines]

def parse_header_line(line):
    for kind, pattern in HEADER_PATTERNS:
        match = re.match(pattern, line)
        if match:
            return (kind, line, match)
    return None

def parse_line(line):
    if not line.strip():
        return (BLANK, '\n', None)
    for kind, pattern in PATTERNS:
        match = re.match(pattern, line)
        if match:
            return (kind, line, match)
    return (LINE, line.replace('\n', ' '), None)


def parse(lines):
    lines = parse_lines(lines)

    head = parse_head(lines) # end_line
    entries = parse_body(body(lines)) # start_line
    return head, entries

def main(args):
    fin = open(args[1], 'r')
    lines = fin.readlines()
    fin.close()
    # print lines
    head, entries = parse(lines)
    print head
    for entry in entries:
        print entry, '\n'
    return 0

if __name__ == "__main__":
    main(sys.argv)