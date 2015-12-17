import csv
import re
import xml.etree.ElementTree as ET

from utils import add_membership, data_path, idFactory, REASONS, PROVINCES


def FixingDictReader(data):
    for row in csv.DictReader(data):
        yield dict((key, fix_bad_encoding(value)) for key, value in row.items())

def fix_bad_encoding(s):
    if s is None: return s
    s = s.decode('utf-8')
    if u'\u00e9' in s or u'\u00e4' in s:
        return s # A couple of entries are not double-encoded
    if u'\u0192' in s:
        # Corrupt and triple-encoded
        s = s.encode('raw_unicode_escape').replace(r'\u0192', '\x83').decode('utf-8')
    s = s.encode('raw_unicode_escape').decode('utf-8')
    return s

# MyReps CSV dump

def col_map(c):
    if c == 'first_name': return 'given_names'
    if c == 'last_name': return 'family_name'
    if c == 'title': return 'honorific_prefix'
    if c == 'position': return 'role'
    return c

def fix_person_bits(person_bits):
    """Fix a few alternate names to be consistent"""
    n = person_bits['given_names']
    if n == 'Nomaindiya Cathleen': person_bits['given_names'] = 'NomaIndiya Cathleen'
    if n == 'Buoang Lemias': person_bits['given_names'] = 'Budang Lemias'
    if n == 'Arthur': person_bits['given_names'] = 'Robert Alfred'
    if 'email' in person_bits and 'dschafer@parliament' in person_bits['email']: del person_bits['email']

def fix_end_reason(position_bits, person_bits):
    """Fix some incorrect end date/reasons"""
    if person_bits['given_names'] == 'Kenneth Raselabe Joseph' and position_bits['organisation'] == 'National Assembly':
        position_bits.update(end_date='2013-06-21', end_reason='2')
    elif person_bits['given_names'] == 'Mathole Serofo' and person_bits['family_name'] == 'Motshekga' and position_bits.get('role') == 'Chief Whip of the Majority Party':
        position_bits.update(end_date='2013-06-20', end_reason='2')
    if 'end_date' not in position_bits: return
    if person_bits['given_names'] == 'Seiso Joel' and position_bits['end_date'] == '2013-03-26': position_bits['end_reason'] = '2'
    elif person_bits['given_names'] == 'Ntombikayise Nomawisile' and position_bits['end_date'] == '2011-10-28': position_bits['end_reason'] = '2'
    elif person_bits['given_names'] == 'Patricia' and position_bits['end_date'] == '2010-09-10': position_bits['end_reason'] = '2'
    elif person_bits['family_name'] == 'Padayachie' and position_bits['end_date'] == '2012-03-05': position_bits['end_date'] = '2012-05-05'

ORGANIZATIONS = {
    'National Assembly': { 'id': 'org.mysociety.za/house/national-assembly', 'name': 'National Assembly', 'slug': 'national-assembly', 'classification': 'house' },
    'National Council of Provinces': { 'id': 'org.mysociety.za/house/ncop', 'name': 'National Council of Provinces', 'slug': 'ncop', 'classification': 'house' },
    'National Executive': { 'id': 'org.mysociety.za/national-executive', 'name': 'National Executive', 'slug': 'national-executive', 'classification': 'executive' },
}
PEOPLE = {}

def parse():
    for row in FixingDictReader(open(data_path + 'myreps_na_executive_export.csv')):
        person_bits = dict((col_map(k),v) for k,v in row.items() if k in ('first_name','last_name','initials_alt','other_names','title','email') and v)
        position_bits = dict((col_map(k),v) for k,v in row.items() if k in ('start_date','end_date','end_reason','organisation','position','region') and v and v != 'Member' and v != 'National')
        if 'end_date' not in position_bits: del position_bits['end_reason']
        if 'end_date' in position_bits and position_bits['end_reason'] == '0': del position_bits['end_reason']

        if person_bits['given_names'] == 'Tlhalefi Andries': continue # Comes in elsewhere
        # Manual fixes of file
        fix_person_bits(person_bits)
        fix_end_reason(position_bits, person_bits)

        name = '%(given_names)s %(family_name)s' % person_bits

        person_bits['name'] = name
        if person_bits.get('email'):
            person_bits['contact_details'] = [ { 'type': 'email', 'value': person_bits.pop('email') } ]
        if 'other_names' in person_bits:
            person_bits['other_names'] = [ { 'name': person_bits['other_names'] } ]

        if position_bits['organisation'] not in ORGANIZATIONS:
            ORGANIZATIONS.setdefault(position_bits['organisation'], {
                'id': 'org.mysociety.za/party/' + position_bits['organisation'].lower(),
                'name': position_bits['organisation'],
                'slug': position_bits['organisation'].lower(),
                'classification': 'party'
            } )
        position_bits['organization_id'] = ORGANIZATIONS[position_bits['organisation']]['id']
        del position_bits['organisation']
        if position_bits['organization_id'] == 'org.mysociety.za/house/national-assembly' and 'role' not in position_bits:
            position_bits['label'] = position_bits['role'] = 'Member'
        elif position_bits['organization_id'] == 'org.mysociety.za/house/ncop':
            position_bits['label'] = position_bits['role'] = 'Delegate'
        if 'end_reason' in position_bits:
            position_bits['end_reason'] = REASONS[position_bits['end_reason']]
        if position_bits.get('region'):
            r = position_bits['region']
            position_bits['area'] = { 'id': 'org.mysociety.za/mapit/code/p/' + PROVINCES[r], 'name': r }
            position_bits['label'] += ' for ' + r
            del position_bits['region']

        if name in PEOPLE:
            person_bits['id'] = PEOPLE[name]['person']['id']
            assert PEOPLE[name]['person'] == person_bits
        else:
            person_bits['id'] = idFactory.new('person')
            PEOPLE[name] = { 'id': person_bits['id'], 'person': person_bits }
        add_membership(PEOPLE[name], position_bits)

    # National Assembly MyReps site data
    # To fetch myreps ID and PERSON_ID

    na = open(data_path + 'myreps-na.xml').read()
    people = ET.fromstring(na).iter('Members')
    cols_xml = [ 'id', 'person_id', 'person_first_name', 'person_last_name', 'person_paries' ]

    for person in people:
        row = dict(zip(cols_xml, [ person.find(x).text for x in cols_xml ]))
        if row['person_first_name'] == 'Nomaindiya Cathleen':
            row['person_first_name'] = 'NomaIndiya Cathleen'
        if row['person_first_name'] == 'Alpheus' and row['person_last_name'] == 'Mokabhe':
            row.update(person_first_name='Alpheus Mokabhe', person_last_name='Maziya')
        if row['person_first_name'] == 'Ximbi':
            row.update(person_first_name='Dumsani Livingstone', person_last_name='Ximbi')
        name = '%(person_first_name)s %(person_last_name)s' % row
        name = fix_bad_encoding(name.encode('utf-8'))
        PEOPLE[name]['person']['identifiers'] = [
            { 'identifier': row['person_id'], 'scheme': 'myreps_person_id' },
        ]
        if row['id']:
            PEOPLE[name]['person']['identifiers'].append({ 'identifier': row['id'], 'scheme': 'myreps_id' })

    na_prev = open(data_path + 'myreps-national-assembly.html').read()
    na_prev = re.search('<div[^>]*id="past"[^>]*>.*?</div>(?s)', na_prev).group(0)
    for person in re.findall('<li><a href="/people/view/(.*?)">([^<]*) ([^<]*?)</a> until .*?</li>', na_prev):
        row = dict(zip(cols_xml, [ '', person[0], person[1], person[2], '' ]))
        if row['person_first_name'] == 'Patricia de':
            row.update(person_first_name='Patricia', person_last_name='de Lille')
        if row['person_first_name'] == 'D van der':
            row.update(person_first_name='D', person_last_name='van der Walt')
        name = '%(person_first_name)s %(person_last_name)s' % row
        PEOPLE[name]['person']['identifiers'] = [
            { 'identifier': row['person_id'], 'scheme': 'myreps_person_id' },
        ]

    # NCOP MyReps site data

    ncop = open(data_path + 'myreps-ncop.xml').read()
    people = ET.fromstring(ncop).iter('Members')
    for person in people:
        row = dict(zip(cols_xml, [ person.find(x).text for x in cols_xml ]))
        # Change couple of names to match parliament data
        if row['person_first_name'] == 'Arthur':
            row['person_first_name'] = 'Robert Alfred'
        elif row['person_first_name'] == 'Buoang Lemias':
            row['person_first_name'] = 'Budang Lemias'
        name = '%(person_first_name)s %(person_last_name)s' % row
        id = idFactory.new('person')
        PEOPLE[name] = {
            'id': id,
            'person': {
                'id': id,
                'given_names': row['person_first_name'],
                'family_name': row['person_last_name'],
                'name': name,
                'identifiers': [
                    { 'identifier': row['id'], 'scheme': 'myreps_id' },
                    { 'identifier': row['person_id'], 'scheme': 'myreps_person_id' },
                ]
            },
        }
        add_membership(PEOPLE[name], { 'organization_id': 'org.mysociety.za/house/ncop', 'label': 'Delegate', 'role': 'Delegate' })
        if row['id'] == '7852':
            # Special case of one person resigned since data
            PEOPLE[name]['memberships'][0].update(
                end_date='2013-03-27', end_reason='Resigned',
                label='Delegate for Eastern Cape',
                area={ 'id': 'org.mysociety.za/mapit/code/p/' + PROVINCES['Eastern Cape'], 'name': 'Eastern Cape' }
            )
        if row['person_paries']:
            add_membership(PEOPLE[name], { 'organization_id': ORGANIZATIONS[row['person_paries']]['id'] })

    for name in PEOPLE.keys():
        PEOPLE[name]['person'].update( memberships = PEOPLE[name]['memberships'] )
        PEOPLE[name] = PEOPLE[name]['person']
        
    return {
        'persons': PEOPLE,
        'organizations': ORGANIZATIONS,
    }

