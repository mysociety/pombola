import re
import requests
import requests_cache
import urllib
import urlparse

from utils import add_membership, idFactory, PROVINCES


requests_cache.install_cache()

def fix_url(url):
    # The path component of the URLs in the current South African
    # Popolo JSON have Unicode characters that need to be UTF-8
    # encoded and percent-escaped:
    parts = urlparse.urlsplit(url)
    fixed_path = urllib.quote(parts.path.encode('UTF-8'))
    parts = list(parts)
    parts[2] = fixed_path
    url = urlparse.urlunsplit(parts)
    # A hash in the URL is really actually not.
    url = url.replace('#', '%23')
    return url

class Person:
    def __init__(self, existing, organizations):
        self.data = existing
        self.organizations = organizations

    def parse_parl(self, data):
        name = '%(given_names)s %(family_name)s' % data
        if not self.data:
            self.data.update(data)
            del self.data['party_id']
            del self.data['party_name']
            del self.data['email']
            self.data['id'] = idFactory.new('person')
            self.data['name'] = name
        assert self.data['name'] == name
        self.data.setdefault('identifiers', []).insert(0, { 'scheme': 'za.gov.parliament/person', 'identifier': '%(id)s' % data } )
        if data.get('email'):
            if 'contact_details' in self.data:
                assert data['email'] == [ x for x in self.data['contact_details'] if x['type'] == 'email' ][0]['value']
            else:
                self.data['contact_details'] = [ { 'type': 'email', 'value': data['email'] } ]

        party = self.organizations[data['party_name']]
        if 'identifiers' in party:
            assert party['identifiers'][0]['identifier'] == data['party_id']
        else:
            party['identifiers'] = [ { 'scheme': 'za.gov.parliament/party', 'identifier': data['party_id'] } ]

        existing_party = [ x for x in self.data.get('memberships', []) if 'party' in x['organization_id'] ]
        if existing_party:
            assert party['id'] == existing_party[0]['organization_id'], party['id']
        else:
            add_membership( self.data, { 'person_id': self.data['id'], 'organization_id': party['id'] } )

        self.text = requests.get('http://www.parliament.gov.za/live/content.php?Item_ID=184&MemberID=%(id)s' % data).text
        self.parse_honorific()
        self.parse_table()
        self.parse_photo()
        self.parse_committees()

    def parse_honorific(self):
        """The individual page is the only place Mr/Mrs/Dr etc is given,
           so extract it from there."""
        title_name = re.search('<p><B class="darker"> *(.*?) *</B>', self.text).group(1)
        if 'Ximbi' in title_name:
            title_name = title_name.replace('Dumsani Livingstone Ximbi', 'Ximbi Dumsani Livingstone')
        title_name_first = title_name.split()[0]
        if title_name_first in ('Mr', 'Mrs', 'Ms', 'Dr', 'Nkosi/Adv', 'Prof', 'Adv', 'Prince'):
            self.data['honorific_prefix'] = title_name_first
            assert title_name == '%(honorific_prefix)s %(family_name)s %(given_names)s' % self.data, title_name
        else:
            assert title_name == '%(family_name)s %(given_names)s' % self.data

    def parse_table(self):
        m = re.findall('<td height="25" valign="middle" class="pad"><b>(.*?):</b></td>\s*<td width="70%" valign="middle" class="pad">(.*?)</td>(?s)', self.text)
        m = dict((k,v) for k, v in m if v not in ('-', '<a href = mailto:></a>'))

        for contact_detail in ('Constituency Fax Number', 'Session Fax Number', 'Cell Phone Number', 'Constituency Phone Number', 'Session Phone Number', 'Constituency Postal Address', 'Constituency Street Address'):
            if contact_detail in m:
                if '<a target' in m[contact_detail]: continue
                if 'Fax' in contact_detail: type = 'fax'
                elif 'Cell' in contact_detail: type = 'cell'
                elif 'Number' in contact_detail: type = 'voice'
                elif 'Address' in contact_detail: type = 'address'
                self.data.setdefault('contact_details', []).append( { 'type': type, 'value': m.pop(contact_detail), 'note': contact_detail } )

        house = self.organizations[m.pop('House')]['id']
        province = None
        if 'Delegate of Province' in m:
            province = m.pop('Delegate of Province')
            label = 'Delegate'
        elif 'Province' in m:
            province = m.pop('Province')
            label = 'Member'

        if self.data['name'] in ('Nqabayomzi Lawrence Kwankwa', 'Cassel Charlie Mathale', 'Wayne Maxim Thring'):
            label = 'Member'

        existing_house = [ x for x in self.data['memberships'] if 'house' in x['organization_id'] ]
        if existing_house:
            assert existing_house[0]['organization_id'] == house
            if province:
                if 'area' in existing_house[0]:
                    assert existing_house[0]['area']['name'] == province
                else:
                    existing_house[0]['area'] = {
                        'id': 'org.mysociety.za/mapit/code/p/' + PROVINCES[province], 'name': province
                    }
                    existing_house[0]['label'] = label + ' for ' + province
        else:
            # Faku
            dat = {
                'person_id': self.data['id'],
                'organization_id': house,
                'role': label,
                'label': label
            }
            if province:
                dat['label'] = label + ' for ' + province
                dat['area'] = { 'id': 'org.mysociety.za/mapit/code/p/' + PROVINCES[province], 'name': province }
            add_membership(self.data, dat)

        if 'Position(s)' in m:
            posns = [ { 'role': x.strip() } for x in m.pop('Position(s)').split('<br />') if x.strip() != 'Delegate' ]
            if len(posns) == 1 and posns[0]['role'] == 'Correctional Services':
                posns[0]['role'] = 'Minister of ' + posns[0]['role']
            elif len(posns) == 1 and posns[0]['role'] == 'Public Service and Administration':
                posns[0]['role'] = 'Minister for the ' + posns[0]['role']
            elif len(posns) == 2 and posns[0]['role'] == 'Minister in The Presidency' and posns[1]['role'] == 'Performance Monitoring and Evaluation as well as Administration in the Presidency':
                posns = [ { 'role': 'Minister in The Presidency: Performance, Monitoring and Evaluation as well as Administration' } ]
            posns = [ x for x in posns if 'Minister' not in x['role'] and x['role'] not in ('Deputy President', 'The Chief Whip of the Opposition', 'House Chairperson', 'Leader Of Opposition', 'Chief Whip of the Opposition', 'Deputy Speaker of the National Assembly', 'Speaker of the National Assembly' ) ] # These come from step 1
            for p in posns:
                p.update(person_id=self.data['id'], organization_id=house)
                add_membership(self.data, p)

    def parse_photo(self):
        m = re.search('<td width=80 valign=top>\s*<img src="([^"]*)" />', self.text)
        if m:
            self.data['image'] = fix_url(m.group(1))

    def parse_committees(self):
        m = re.search('<td[^>]*><b[^>]*>Committees represented on: *</b></td>.*?<table[^>]*>(.*?)</table>(?s)', self.text)
        committees = dict(re.findall('<a href="content.php\?Item_ID=\d+&CommitteeID=(\d+)">(.*?)</a>', m.group(1)))
        for id, name in reversed(committees.items()):
            if name in self.organizations:
                assert self.organizations[name]['id'] == 'org.mysociety.za/committee/' + id
            else:
                self.organizations[name] = {
                    'id': 'org.mysociety.za/committee/' + id,
                    'name': name,
                    'identifiers': [ { 'scheme': 'za.gov.parliament/committee', 'identifier': id } ],
                    'slug': name.lower().replace(' ','-'),
                    'classification': 'committee'
                }
            add_membership(self.data, { 'person_id': self.data['id'], 'organization_id': self.organizations[name]['id'] } )

def parse(data):
    """Fetches the list of NA/NCOP members from Parliament's website, parse
    into structured data. This is for contact details, images, some
    positions."""

    r = requests.get('http://www.parliament.gov.za/live/content.php?Category_ID=97').text
    cols = ('id', 'family_name', 'given_names', 'party_id', 'party_name', 'email')
    for row in re.findall('<tr bgcolor="#FFFFFF">\s+<td height="30" valign="middle" class="pad"><a href="content.php\?Item_ID=184&MemberID=(.*?)">(.*?)<br></a></td>\s+<td valign="middle">&nbsp;</td>\s+<td valign="middle" class="pad">(.*?)</td>\s+<td valign="middle">&nbsp;</td>\s+<td valign="middle" class="pad"><a href="content.php\?Item_ID=219&PartyID=(.*?)">(.*?)</a></td>\s+<td valign="middle">&nbsp;</td>\s+<td align="left" valign="middle" class="pad"> <a href="mailto:(.*?)">(.*?)</a></td>', r):
        row = dict(zip(cols, row))
        if row['family_name'] == 'Mokabhe' and row['given_names'] == 'Alpheus': continue # Dupe
        if row['id'] == 'id': continue # 2nd header
        if row['given_names'] == 'Ximbi':
            row.update(given_names='Dumsani Livingstone', family_name='Ximbi')
        name = '%s %s' % (row['given_names'], row['family_name'])
        if 'Faku' in name or name in ('Kesenkamang Veronica Kekesi', 'Nqabayomzi Lawrence Kwankwa', 'Cassel Charlie Mathale', 'Wayne Maxim Thring'):
            data['persons'][name] = {}
        person = Person(data['persons'][name], data['organizations'])
        person.parse_parl(row)

    return data
