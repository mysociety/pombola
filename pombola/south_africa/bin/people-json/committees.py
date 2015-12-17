import csv
import re
import unicodedata

from utils import add_membership, data_path, idFactory


def initialise(name):
    return re.sub('[^A-Z]', '', name)

def asciify(name):
    return unicodedata.normalize('NFKD', unicode(name)).encode('ascii', 'ignore')

def parse(data):
    orgs_by_id = dict([ (x['id'], x) for x in data['organizations'].values() ])

    # TODO: Perhaps check old/new committees, then stop using parl.py
    # committees. Or just assume these new ones are accurate.
    for row in csv.DictReader(open(data_path + 'committees.csv')):
        if row['Name'] not in data['organizations']:
            data['organizations'][row['Name']] = {
                'id': idFactory.new('committee_pmg'),
                'name': row['Name'],
                'slug': row['Name'].lower().replace(' ','-'),
                'classification': row['Type']
            }

    for row in csv.DictReader(open(data_path + 'committee-members.csv')):
        row['Name'] = re.sub('^([^,]*) Mr, (.*)$', r'\1, Mr \2', row['Name'])

        family_name, initials = row['Name'].split(',')
        initials = re.sub('^\s*(Mr|Ms|Dr|Nkosi|Prof|Adv|Prince)\s+', '', initials)

        # TODO: Use the person's other_names filed, and get these misspellings in there.
        if family_name == 'Khorai': family_name = 'Khoarai'
        if family_name == 'Hoosan': family_name = 'Hoosen'
        if family_name == 'Jeffrey': family_name = 'Jeffery'
        if family_name == 'Hill-Lews': family_name = 'Hill-Lewis'
        if family_name == 'Koornhof' and initials == 'NC': initials = 'NJJVR'

        matches = [ x for x in data['persons'].values() if asciify(x['family_name']) == family_name ]
        if len(matches) > 1:
            matches = [ x for x in data['persons'].values() if x['family_name'] == family_name and initialise(x['given_names']) == initials ]
            if not matches:
                matches = [ x for x in data['persons'].values() if x['family_name'] == family_name and initialise(x['given_names'])[0:len(initials)] == initials ]

        # With the current data, we now always have one result 
        assert len(matches) == 1
        person = matches[0]

        party = [ x for x in person['memberships'] if 'party' in x['organization_id'] ][0]['organization_id']
        assert row['Party'] == orgs_by_id[party]['name'], row['Party'] + orgs_by_id[party]['name']

        mship = {
            'organization_id': data['organizations'][row['Committee']]['id']
        }
        if row['IsAlternative?'] == 'True':
            mship['role'] = 'Alternate Member'
        if row['IsChairperson?'] == 'True':
            mship['role'] = 'Chairperson'
        add_membership(person, mship)

    return data
