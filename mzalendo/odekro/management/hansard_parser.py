import sys
import re
import datetime

# Constants for various types of line that might be found in the transcript
BLANK            = 'blank'
SERIES_VOL_NO    = 'series volume number'
TIME             = 'time'
DATE             = 'date'
START_TIME       = 'start time'
HEADING          = 'heading'
LINE             = 'line'
SCENE            = 'scene'
SPEECH           = 'speech'
ACTION           = 'action'
PAGE_HEADER      = 'page header'
CONTINUED_SPEECH = 'continued speech'
CHAIR            = 'chair'
SCENE_START      = 'scene_start'
SCENE_END        = 'scene_end'
ADJOURNMENT      = 'adjournment'

PRINTED_BY_MARKER = 'printed by department of official report'

SERIES_VOL_NO_PATTERN = r'^\s*([A-Z]+)\s+SERIES\s+VOL\.?\s*(\d+)\s*N(O|o|0)\.?\s*(\d+)\s*$'
DATE_PATTERN = r'^\s*([A-Za-z]+\s*,\s*)?(\d+)\w{0,2}\s+(\w+),?\s+(\d+)\s*$'

TITLES_TEMPLATE = '(Mr|Mrs|Ms|Miss|Papa|Alhaji|Madam|Dr|Prof|Chairman|Chairperson|Minister|An Hon Mem|Some Hon Mem|Minority|Majority|Nana)'
TIME_TEMPLATE = '(\d\d?)(:|\.)(\d\d)\s*(am|a.\s*m|AM|A.\s*M|pm|PM|p.\s*m|P.\s*M|noon)\.?[\s\-]*'
VOTES_AND_PROCEEDINGS_HEADER = '(\s*Votes and Proceedings and the Official Report\s*)'

HEADING_PATTERN = r'^\s*([A-Z-,\s]+|%s)\s*$' % VOTES_AND_PROCEEDINGS_HEADER
SCENE_PATTERN = r'^\s*(\[[A-Za-z-\s]+\])\s*$'
SPEECH_PATTERN = r'^\s*%s([^:;{}"\[\]]+):\s*(.*)\s*$' % TITLES_TEMPLATE
CONTINUED_SPEECH_PATTERN = r'^\s*\[%s.+\]\s*' % (TITLES_TEMPLATE.upper())

SCENE_START_PATTERN = r'^\s*(\[[^\]]+)\s*$'
SCENE_END_PATTERN = r'^\s*([^\]]*\])\s*$'

#POSSIBLE_SPEECH_PATTERN = r'^\s*%s(.+)\s*$' % TITLES_TEMPLATE
#PAGE_HEADER_PATTERN =r'^(\d+)\s*(.*?)(\d{2}\s*\w*,\s*\d{4})(\s*.*?\s*)(\d+)\s*$'

PAGE_HEADER_PATTERN = r'^\[(\d+)\]\s*$'

ACTION_PATTERN = r'^\s*%s(.+\w)\s*[\-]+\s*([^-]+)\s*[\-]+\s*$' % TITLES_TEMPLATE

START_TIME_PATTERN = r'The\s+House\s+met\s+at\s+%s' % TIME_TEMPLATE
TIME_PATTERN = r'^\s*%s$' % TIME_TEMPLATE

CHAIR_PATTERN = r'^\[\s*(.*?)\s+IN\s+THE\s+CHAIR\s*\]$'

#WEEKDAY_TEMPLATE ='(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'
#DATE_SUFFIX_TEMPLATE ='(st|ST|nd|ND|rd|RD|th|TH)'
#LONG_DATE_PATTERN = r'^%s[,]?\s+\d+%s\w+,\d{4}'%(WEEKDAY_TEMPLATE,DATE_SUFFIX_TEMPLATE)
ADJOURNMENT_PATTERN = r'^The\s+House\s+was\s+(accordingly\s+)?adjourned\s+at\s+(%s)\s+till\s+(.*)\s+at\s+(%s).*\s*$'%(TIME_TEMPLATE,TIME_TEMPLATE)

MONTHS = dict(jan=1, feb=2, mar=3, apr=4, may=5, jun=6, 
              jul=7, aug=8, sep=9, oct=10, nov=11, dec=12)

ORDINAL_WORDS = dict(first=1, second=2, third=3, fourth=4, fifth=5,
                     sixth=6, seventh=7)


HEADER_PATTERNS = (
    (DATE, DATE_PATTERN),
    (SERIES_VOL_NO, SERIES_VOL_NO_PATTERN),
    (TIME, START_TIME_PATTERN),
)

PATTERNS = (
    (SPEECH, SPEECH_PATTERN),
    (HEADING, HEADING_PATTERN),
    (TIME, TIME_PATTERN),
    (START_TIME, START_TIME_PATTERN),
    (PAGE_HEADER, PAGE_HEADER_PATTERN),
    (CHAIR, CHAIR_PATTERN),
    (CONTINUED_SPEECH, CONTINUED_SPEECH_PATTERN),
    (SCENE, SCENE_PATTERN),
    (ACTION, ACTION_PATTERN),
    (SCENE_START, SCENE_START_PATTERN),
    (SCENE_END, SCENE_END_PATTERN),
    (ADJOURNMENT, ADJOURNMENT_PATTERN),
)


def parse(content):
    lines = normalised_lines(content)
    lines = scan(lines)
        
    head = parse_head(lines) # end_line
    entries = parse_body(body(lines)) # start_line
    return head, entries

def scan(lines, header=True):
    if header:
        return [scan_header_line(x) or scan_line(x) for x in lines]
    return [scan_line(x) for x in lines]

def parse_head(lines):
    """
    Parse the document to extract the header information. Returns a dict.
    """

    series = volume = number = date = time = None
    
    for i, row in enumerate(lines):
        # print row
        kind, line, match = row
        if SERIES_VOL_NO == kind:
            series = ORDINAL_WORDS[match.group(1).lower()]
            volume = int(match.group(2))
            number = int(match.group(4))
        elif DATE == kind and not date:
            date = datetime.date(int(match.group(4)),
                                 MONTHS[match.group(3).lower()[:3]], 
                                 int(match.group(2)))
        elif TIME == kind and not time:
            time = parse_time(''.join(match.groups()))
        if series and volume and number and date and time:
            break

    return dict(
        series = series,
        volume = volume,
        number = number,
        date   = date,
        time   = time,
    )

def parse_body(lines):
    entries = []
    
    time = None
    topic = None
    #page = None
    column = None
    section = None
    kind, line, match = None, None, None

    while len(lines):

        kind, line, match = lines.pop(0)        
        
        # store any entry details here. Later we'll add common fields as required
        entry = None
        
        if kind is LINE:
            if len(entries) and entries[-1].get('name', None):
                    kind = SPEECH
                    entry = entries.pop(-1)
                    entry['speech'] = '%s\n\n%s' % (entry.get('speech'), line.strip())
        elif kind is BLANK:
            pass

        elif kind is SPEECH:
            speech = parse_speech(time, match, lines)
            entry = dict(speech.items() + dict(section=section, column=column).items())
        elif kind is HEADING:
            section = line.strip().upper()
            entry = dict(heading=line.strip().upper(), column=column)
        elif kind in (TIME, START_TIME):
            time = _time(match)
        elif kind is ACTION:
            person = '%s%s' % (match.group(1), match.group(2))
            entry = dict(action=match.group(3), name=person.strip(), column=column)
        elif kind is PAGE_HEADER:
            # pages = '%s' % (match.group(1))
            column = match.group(1) 
            #title = '%s%s' % (match.group(2),match.group(4))
            #entries.append(dict(page=pages))
        elif kind is SCENE_START:
            entry = parse_scene(time, match, lines, line)
            entry['column'] = column
            # hack to catch chair on multiple lines
            m = re.match(CHAIR_PATTERN, entry['scene'])
            if m:
                kind = CHAIR
                entry = dict(chair=m.group(1), 
                             original=entry['original'], column=column)
            else:
                kind = SCENE

        elif kind is CONTINUED_SPEECH:
            if len(entries):
                prev_entry = entries[-1]

                if prev_entry.get('name'):
                    speech = parse_speech(time, match, lines,name=prev_entry['name'])
                    entry = dict(speech.items() + \
                                 dict(section=section, column=column).items())
        
        elif kind is CHAIR:
            entry = dict(chair=match.group(1), original=line, column=column)
        elif kind is ADJOURNMENT:
            entry = dict(scene=line, original=line,column=column)
            kind = SCENE
            time = _time(re.match(TIME_PATTERN,match.group(2)))
        else:
            # print "skipping '%s': '%s'" % ( kind, line )
            pass
        
        if entry:

            entry['time']     = time
            entry['kind']     = kind
            # entry['column']   = column
            if not entry.get('original', None):
                entry['original'] = line.rstrip()
            elif entry['kind'] not in (SCENE, CHAIR):
                entry['original'] = '%s\n%s' % (entry['original'], line.strip())
            entries.append(entry)

    return entries


def chair(match, line, column):
    return dict(chair=match.group(1), original=line, column=column) 


def parse_scene(time, match, lines, line=''):
    scene = match.group(1)
    original = line.strip()

    while len(lines):
        kind, line, match = lines.pop(0)
        
        original += '\n' + line.strip()
        
        if kind == SCENE_END:
            scene += ' ' + line.strip()
            break
        elif kind == LINE:
            scene += ' ' + line.strip()
        elif kind == BLANK:
            pass
        else:
            lines.insert(0, (kind, line, match))
            break
    return dict(scene=scene.strip(), original=original)

def parse_speech(time, match, lines, name=None):
    """A speech has the ff properties:
    1. Starts with a member's name followed by a colon
    2. Is followed by a number of LINEs or BLANKs
    3. May be continued on a new page [page#] [scene]
    """
    if name == None:
        name, speech = speech_match_parts(match)
    else:
        speech = ''

    kind, line, match = None, None, None
    newpage = False

    while len(lines):
        kind, line, match = lines.pop(0)
        if kind == LINE: 
            speech += ' ' + line
        elif kind == BLANK:
            speech = speech.strip() + '\n'
        else:
            # put the line back on the lines
            lines.insert(0, (kind, line, match))
            break

    return dict(time=time, name=name, speech=speech.strip())


def speech_match_parts(match):
    try:
        name = '%s%s' % (match.group(1), match.group(2))
        speech = match.group(3)
        return (name, speech)
    except: pass
    return (None, None)

def parse_time(s):
    match = re.match(TIME_PATTERN, s)
    if match:
        return _time(match)
    return None

def _time(match):
    hh, mm = int(match.group(1)), int(match.group(3))
    t = match.group(4)
    if t.lower() in ('pm', 'p.m') and hh != 12:
        hh += 12
    return datetime.time(hh, mm)

def scan_header_line(line):
    for kind, pattern in HEADER_PATTERNS:
        match = re.match(pattern, line)
        if match:
            return (kind, line, match)
    return (LINE, line.replace('\n', ' '), None)

def scan_line(line):
    if not line.strip():
        return (BLANK, '\n', None)
    for kind, pattern in PATTERNS:
        match = re.match(pattern, line)
        if match:
            if kind == CONTINUED_SPEECH and 'in the chair' in line.lower():
                return (SCENE, line, match)
            elif kind == SPEECH_PATTERN:
                name, speech = speech_match_parts(match)
                if name and len(name) >= 100:
                    break
            return (kind, line, match)
    return (LINE, line.replace('\n', ' '), None)

def meta(lines):
    xs = []
    for line in lines:
        if line.lower().strip().startswith(PRINTED_BY_MARKER):
            break
        xs.append(line)
    return xs

def body(lines):
    """Returns lines in the body of the hansard"""
    for i, row in enumerate(lines):
        _, line, _ = row
        #if line.lower().strip().startswith('the house met at'):
        if line.lower().strip().startswith(PRINTED_BY_MARKER):
            return lines[i:] #[x for x in lines[i:]]
    # return [x for x in lines] ??
    return lines

def normalised_lines(content):
    return normalise_line_breaks(preprocess(content)).split("\n")

def normalise_line_breaks(content):

    # Each tuple is a (pattern, replacement) to apply to the string, in the
    # order listed here. Note that the re.M flag is applied so that ^ and $
    # DWIM.
    transformations = [

        # make whitespace consistent
        ( r'\r',     '\n' ), # convert any vertical whitespace to '\n'
        ( r'[ \t]+', ' '  ), # horizontal whitespace becomes single space
        ( r' *\n *', '\n' ), # trim spaces from around newlines
        
        # Add breaks around the column numbers
        ( r'\s*(\[\d+\])\s*', r"\n\n\1\n\n" ),
        
        # Add breaks around anything that is all in CAPITALS
        ( r'^([^a-z]+?)$', r"\n\n\1\n\n" ),
        # not sure why the '+?' can't just be '+' - if it is just '+' the
        # newline gets included too despite the re.M. Pah!

        # Add break before things that look like lists
        ( r'^([ivx]+\))', r'\n\n\1' ),

        # Add breaks around timestamps
        ( r'^(%s)$' % TIME_TEMPLATE, r"\n\n\1\n\n"),
        # ( DATE_PATTERN, r"\n\n\1\n\n"),
        
        (SERIES_VOL_NO_PATTERN, r'\n\n\1 SERIES VOL \2 No. \4\n\n'),

        # Add a break before anything that looks like it might be a person's
        # name at the start of a speech
        ( r'^(%s.+:)' % TITLES_TEMPLATE, r'\n\n\1' ),
        
        # Finally normalise the whitespace
        ( r'(\S)\n(\S)', r'\1 \2' ), # wrap consecutive lines
        ( r'\n\n+', "\n\n" ),        # normalise line breaks
    ]

    # apply all the transformations above
    for pattern, replacement in transformations:
        content = re.sub( pattern, replacement, content, flags=re.M )
    
    return content.strip()

def preprocess(content):
    # hack to clear newlines and other chars we are seeing in some of the content
    content = '\n'.join([x.strip().decode('utf8','ignore') for x in content.splitlines()])
    # content = u'%s' % content
    # content = content.decode('utf8')
    content = ''.join(content.split(u'\xaf'))
    # content = content.decode('utf8')
    for s, r in [(u'\u2013', '-'), (u'\ufeff', ''), 
                 (u'O\ufb01icial', 'Official'), 
                 (u'Of\ufb01cial', 'Official'), 
                 (u'\ufb01', 'fi'), (u'\ufb02', 'ff'), ('~', '-')]:
        content = r.join(content.split(s))
    return content

def main(args):
    fin = open(args[1], 'r')
    content = fin.read()
    fin.close()
    # print content
    head, entries = parse(content)
    print head
    for entry in entries:
        print entry, '\n'
    return 0

if __name__ == "__main__":
    main(sys.argv)
