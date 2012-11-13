import re
from datetime import datetime


def split_name(name):
    m = re.match(r'^\s*([^,]+)\s*,\s*([^\s]+)(\s+[^\(]+)?\s*(\(.+)?', name)
    if m:
        last, first, mid, title = m.group(1) or '', m.group(2) or '', \
                                  m.group(3) or '', m.group(4) or ''
        mid = mid.strip()
        if title:
            title = re.sub(r'\]', ')', re.sub(r'\[', '(', re.sub(r'(\(|\))', '', title).strip()))
        return last, first, mid, title
    return None

def convert_date(s):
    s = re.sub(r'\s*(\w+)\s+(\d{1,2})(st|nd|rd|th)?,\s*(\d+)\s*', 
                '\\1 \\2, \\4', s)
    return datetime.strptime(s, "%B %d, %Y")

def legal_name(last_name, first_name, middle_name=None):
    if middle_name:
        middle_name = ' %s' % middle_name
    else:
        middle_name = ''
    return '%s%s %s' % (first_name, middle_name, last_name)
