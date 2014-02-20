import csv
import datetime
import errno
import hmac
import hashlib
import json
import os
import re
import requests
import sys
import time

from django.conf import settings
from django.template.defaultfilters import slugify

from django_date_extensions.fields import ApproximateDate

from pombola.core.models import Person, Place, PlaceKind, ParliamentarySession, Position, PositionTitle

from django.core.files.base import ContentFile
from pombola.images.models import Image

iebc_base_url = 'http://api.iebc.or.ke'

today_date = datetime.date.today()
today_approximate_date = ApproximateDate(today_date.year,
                                         today_date.month,
                                         today_date.day)

yesterday_date = today_date - datetime.timedelta(days=1)
yesterday_approximate_date = ApproximateDate(yesterday_date.year,
                                             yesterday_date.month,
                                             yesterday_date.day)

# From: http://stackoverflow.com/q/600268/223092

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def file_mtime_iso8601(filename):
    return time.strftime('%Y-%m-%dT%H-%M-%S', time.localtime(os.path.getmtime(filename)))

def make_api_token_url(app_id, api_key):
    """Create the URL that should be used for retrieving an API token"""

    return iebc_base_url + '/token/?appid=%s&key=%s' % (app_id, api_key)

def make_api_url(path, api_secret, token, query_filter=None):
    """Create a URL for a generic query to the API

    This can only be used after you've successfully got a token"""
    if query_filter is None:
        query_filter = ''
    key_string = '%stoken=%s' % (query_filter, token)
    key = hmac.new(api_secret,
                   key_string,
                   hashlib.sha256).hexdigest()
    url = iebc_base_url + path + '?'
    if query_filter:
        url += query_filter + '&'
    url += 'token=%s&key=%s' % (token, key)
    return url

def get_data(url):
    """Make a request to the API with error checking and JSON decoding"""

    r = requests.get(url)
    try:
        data = json.loads(r.text)
    except ValueError:
        print >> sys.stderr, "No valid JSON was found, the response was:"
        print >> sys.stderr, r.text
        raise
    if data['status'] != 'SUCCESS':
        print >> sys.stderr, '  ', data['status']
        print >> sys.stderr, '  ', data['message']
        print >> sys.stderr, '  The URL was:', url
        raise CommandError, "Getting data from the API failed"
    return data

def get_data_with_cache(cache_filename, *args, **kwargs):
    if os.path.exists(cache_filename):
        with open(cache_filename) as fp:
            result = json.load(fp)
    else:
        if kwargs.get('only_from_cache', False):
            raise CommandError, "There was no cached data for %s" % (args[0],)
        else:
            result = get_data(*args, **kwargs)
            with open(cache_filename, 'w') as fp:
                json.dump(result, fp)
    return result

# ------------------------------------------------------------------------

def update_picture_for_candidate(candidate_data, cache_directory, **options):
    picture_intro = 'Picture from the IEBC API for candidate'
    candidate_code = candidate_data['code']
    filename = os.path.join(cache_directory, "candidate-%s.jpg" % (candidate_code,))
    if not os.path.exists(filename):
        image_url = candidate_data['picture']
        r = requests.get(image_url)
        if r.status_code == 200:
            with open(filename, 'w') as fp:
                fp.write(r.content)
    # If that image now exists, use it:
    if os.path.exists(filename):
        # Find the position from the candidate code, so we can get the right person:
        positions = Position.objects.filter(external_id=candidate_code).currently_active()
        if not positions:
            print "#### Missing position for:", candidate_code
        elif len(positions) > 1:
            print "#### Multiple positions for:", candidate_code
        else:
            person = positions[0].person
            if options['commit']:
                # Remove old IEBC images for that person:
                person.images.filter(source__startswith=picture_intro).delete()
                # And now create the new one:
                new_image = Image(
                    content_object = person,
                    source = "%s %s" % (picture_intro, candidate_code))
                with open(filename) as fp:
                    new_image.image.save(
                        name = "%s-%s.jpg" % (candidate_code, file_mtime_iso8601(filename)),
                        content = ContentFile(fp.read()))

# ------------------------------------------------------------------------

# Set up a mapping between the race names and the
# corresponding PlaceKind and Position title:

try:
    known_race_type_mapping = {
        "2": (PlaceKind.objects.get(slug='county'),
              ParliamentarySession.objects.get(slug='s2013'),
              PositionTitle.objects.get(slug__startswith='aspirant-governor'),
              "Governor"),
        "3": (PlaceKind.objects.get(slug='county'),
              ParliamentarySession.objects.get(slug='s2013'),
              PositionTitle.objects.get(slug__startswith='aspirant-senator'),
              "Senator"),
        "5": (PlaceKind.objects.get(slug='county'),
              ParliamentarySession.objects.get(slug='s2013'),
              PositionTitle.objects.get(slug__startswith='aspirant-women-representative'),
              "Women Representative"),
        "4": (PlaceKind.objects.get(slug='constituency'),
              ParliamentarySession.objects.get(slug='na2013'),
              PositionTitle.objects.get(slug__startswith='aspirant-mp'),
              "National Assembly Rep."),
        "6": (PlaceKind.objects.get(slug='ward'),
              ParliamentarySession.objects.get(slug='na2013'),
              PositionTitle.objects.get(slug__startswith='aspirant-ward-representative'),
              "County Assembly Rep."),
        }
except PlaceKind.DoesNotExist:
    # This should only happen if this isn't a Kenya database, but this
    # file will be imported when running tests when you might have the
    # database for any country.  FIXME: switch this to be a function
    # that returns the mapping; this is just a temporary workaround
    # since we're not sure this script will ever be used again, so
    # it's not worth the time to test a better fix.
    known_race_type_mapping = None

def parse_race_name(race_name):
    types_alternation = "|".join(re.escape(krt) for krt in known_race_types)
    m = re.search('^((%s) - )(.*?)\s+\(\d+\)$' % (types_alternation,), race_name)
    if not m:
        raise Exception, "Couldn't parse race:" + race_name
    return (m.group(2), m.group(3))

#------------------------------------------------------------------------

def get_person_from_names(first_names, surname):
    full_name = first_names + ' ' + surname
    first_and_last = re.sub(' .*', '', first_names) + ' ' + surname
    for field in 'legal_name', 'alternative_names__alternative_name':
        for version in (full_name, first_and_last):
            kwargs = {field + '__iexact': version}
            matches = Person.objects.filter(**kwargs)
            if len(matches) > 1:
                message = "  Multiple Person matches for %s against %s" % (version, field)
                print >> sys.stderr, message
                # raise Exception, message
            elif len(matches) == 1:
                return matches[0]
    # Or look for an exact slug match:
    matches = Person.objects.filter(slug=slugify(full_name))
    if len(matches) == 1:
        return matches[0]
    matches = Person.objects.filter(slug=slugify(first_and_last))
    if len(matches) == 1:
        return matches[0]
    return None

def normalize_name(name):
    result = re.sub(',', ' ', name)
    result = re.sub('\s+', ' ', result)
    return result.strip()

def maybe_save(o, **options):
    if options['commit']:
        o.save()
        print >> sys.stderr, 'Saving %s' % (o,)
    else:
        print >> sys.stderr, 'Not saving %s because --commit was not specified' % (o,)

def match_lists(a_list, a_key_function, b_list, b_key_function):
    """Match up identical elements from two list of different lengths

    Return a list of tuples that represent assignments from items in
    a_list to those b_list.  The first tuples will be those where
    a_key_function applied to the element from a_list was equal to
    b_key_function applied to the element from b_list.  After that,
    all the unmatched elements from a_list are listed in the first
    slot of the tuple with None in the second.  Contrariwise, then all
    the unmatched elements from b_list are listed.

    There are bound to be more efficient ways of implementing this,
    but this is at least simple, and it's not being used in
    performance critical situations.

    An example (and doctest):

    >>> list1 = ['fOO', 'bar', 'BAz', 'quux']
    >>> list2 = ['baz', 'quux', 'xyzzy', 'baz']
    >>> match_lists(list1, lambda e: e.lower(), list2, lambda e: e)
    [('BAz', 'baz'), ('quux', 'quux'), ('fOO', None), ('bar', None), (None, 'xyzzy'), (None, 'baz')]
    """

    # Shallow copy the lists, so we can safely remove elements:
    a_list = a_list[:]
    b_list = b_list[:]
    a_keys = set(a_key_function(a) for a in a_list)
    b_keys = set(b_key_function(b) for b in b_list)
    exact_key_matches = a_keys & b_keys
    results = []
    for common_key in sorted(exact_key_matches):
        # For each match, extract it from each list and add the tuple
        # to the results:
        for i, a in enumerate(a_list):
            if a_key_function(a) == common_key:
                matching_element_a = a_list.pop(i)
                break
        for i, b in enumerate(b_list):
            if b_key_function(b) == common_key:
                matching_element_b = b_list.pop(i)
                break
        results.append((matching_element_a, matching_element_b))
    for a in a_list:
        results.append((a, None))
    for b in b_list:
        results.append((None, b))
    return results

# ------------------------------------------------------------------------

class SamePersonChecker(object):

    headings = ['Same/Different',
                'API Name',
                'API Party',
                'API Place',
                'Contest Type',
                'API Candidate Code',
                'Mz Legal Name',
                'Mz Other Names',
                'Mz Candidate Code',
                'Mz URL',
                'Mz Parties Ever',
                'Mz Aspirant Ever',
                'Mz Politician Ever',
                'Mz ID']

    def __init__(self, csv_filename):
        self.csv_filename = csv_filename
        self.same_people_lookup = {}
        self.rows = []
        with open(self.csv_filename) as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                self.rows.append(row)
                classification = row['Same/Different']
                mz_id = int(row['Mz ID'], 10)
                candidate_code = row['API Candidate Code']
                key = (candidate_code, mz_id)
                if re.search('(?i)^Same', classification):
                    self.same_people_lookup[key] = True
                elif re.search('(?i)^Different', classification):
                    self.same_people_lookup[key] = False
                else:
                    raise Exception, "Bad 'Same/Different' value in the line: %s" % (row,)

    def add_possible_match(self,
                           candidate_data,
                           candidate_place,
                           candidate_race_type,
                           mz_person):
        with open(self.csv_filename, 'w') as fp:
            writer = csv.DictWriter(fp, SamePersonChecker.headings)
            writer.writerow(dict((h, h) for h in SamePersonChecker.headings))
            # Write out the existing data first:
            for existing_row in self.rows:
                for k in ('Contest Type', 'Mz Candidate Code'):
                    existing_row[k] = ''
                writer.writerow(existing_row)
                # And now add the new person:
            row = {}
            row['Same/Different'] = ''
            first_names = normalize_name(candidate_data['other_name'] or '')
            surname = normalize_name(candidate_data['surname'] or '')
            row['API Name'] = first_names + ' ' + surname
            party_data = candidate_data['party']
            row['API Party'] = party_data['name'] if 'name' in party_data else ''
            row['API Place'] = '%s (%s)' % (candidate_place.name, candidate_place.kind.name.lower())
            row['Contest Type'] = candidate_race_type
            row['API Candidate Code'] = candidate_data['code']
            row['Mz Legal Name'] = mz_person.legal_name
            row['Mz Other Names'] = "\n".join(an.alternative_name for an in mz_person.alternative_names.all())
            row['Mz Candidate Code'] = ", ".join(mz_person.current_positions_external_ids)
            row['Mz URL'] = 'http://info.mzalendo.com' + mz_person.get_absolute_url()
            row['Mz Parties Ever'] = ', '.join(o.name for o in mz_person.parties_ever())
            for heading, positions in (('Mz Aspirant Ever', mz_person.aspirant_positions_ever()),
                                       ('Mz Politician Ever', mz_person.politician_positions_ever())):
                row[heading] = ', '.join('%s at %s' % (p.title.name, p.place) for p in positions)
            row['Mz ID'] = mz_person.id
            for key, value in row.items():
                row[key] = unicode(value).encode('utf-8')
            writer.writerow(row)
            self.rows.append(row)

    def check_same_and_update(self,
                              candidate_data,
                              candidate_place,
                              candidate_race_type,
                              mz_person):
        key = (candidate_data['code'], mz_person.id)
        if key in self.same_people_lookup:
            return self.same_people_lookup[key]
        else:
            # Otherwise, add this person to the end of the CSV file
            # for checking:
            self.add_possible_match(candidate_data,
                                    candidate_place,
                                    candidate_race_type,
                                    mz_person)
            return None
