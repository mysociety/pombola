import json
import re

from django.utils.text import slugify


class ChangeApplier(object):

    popolo_data = json.loads( open( '../south-africa-popolo.json' ).read() )
    position_data = json.loads( open( 'all_positions.json' ).read() )
    contacts_data = json.loads( open( 'all_contacts.json' ).read() )

    persons = popolo_data['persons']
    organizations = popolo_data['organizations']

    areas = {
        "Eastern Cape" : { "id": "org.mysociety.za/mapit/code/p/EC",  "name": "Eastern Cape"  },
        "Free State"   : { "id": "org.mysociety.za/mapit/code/p/FS",  "name": "Free State"    },
        "Gauteng"      : { "id": "org.mysociety.za/mapit/code/p/GT",  "name": "Gauteng"       },
        "KwaZulu-Natal": { "id": "org.mysociety.za/mapit/code/p/KZN", "name": "KwaZulu-Natal" },
        "Limpopo"      : { "id": "org.mysociety.za/mapit/code/p/LIM", "name": "Limpopo"       },
        "Mpumalanga"   : { "id": "org.mysociety.za/mapit/code/p/MP",  "name": "Mpumalanga"    },
        "Northern Cape": { "id": "org.mysociety.za/mapit/code/p/NC",  "name": "Northern Cape" },
        "North West"   : { "id": "org.mysociety.za/mapit/code/p/NW",  "name": "North West"    },
        "Western Cape" : { "id": "org.mysociety.za/mapit/code/p/WC",  "name": "Western Cape"  },
    }



    membership_base = 'org.mysociety.za/membership/'
    membership_max = 0
    for p in persons:
        for m in p['memberships']:
            id = int(m['id'].replace(membership_base, ''))
            if id > membership_max: membership_max = id

    def get_next_membership_id(self):
        self.membership_max += 1
        return self.membership_base + str(self.membership_max)

    def get_next_id(self, array, base):
        all_numbers = [int(x['id'].replace(base, '')) for x in array if base in x['id']]
        next_number = max(all_numbers) + 1
        return base + str(next_number)


    def get_person(self, name):
        """return the person's entry. If none found create a blank one and append it to the persons array"""
        by_name = dict([(p['name'], p) for p in self.persons])

        if name in by_name:
            return by_name[name]

        person = {
            "id": self.get_next_id(self.persons, 'org.mysociety.za/person/'),
            "name": name,
            "slug": slugify(name),
            "memberships": [],
            "contact_details": [],
        }
        self.persons.append(person)
        return person


    def get_organization(self, name, classification):
        """return the organization's entry. If none found create a blank one and append it to the organizations array"""
        by_name = dict([(o['name'], o) for o in self.organizations])

        if name in by_name:
            return by_name[name]

        org = {
            "classification": slugify(classification),
            "id": "org.mysociety.za/%s/%s" % (slugify(classification), slugify(name)),
            "name": name,
            "slug": slugify(name)
        }
        self.organizations.append(org)
        return org


    def apply_positions(self):
        for pos in self.position_data:
            person = self.get_person(pos['legal_name'])
            org = self.get_organization(pos['organisation_name'], pos['organisation_kind'])

            label = pos['position_title']
            if pos['place_name']:
                label += " for %s" % pos['place_name']

            position = {
                "id": self.get_next_membership_id(),
                "label": label,
                "organization_id": org['id'],
                "person_id": person['id'],
                "role": pos['position_title'],
            }

            if pos['place_name']:
                position['area']= self.areas[pos['place_name']]

            person['memberships'].append(position)


    def apply_contact_details(self):
        for cd in self.contacts_data:
            person = self.get_person(cd['legal_name'])

            contact_detail = {
                "type":  cd['contact_type'],
                "value": cd['contact_detail'],
            }

            person['contact_details'].append(contact_detail)


    def run (self):
        self.apply_positions()
        self.apply_contact_details()
        self.write()


    def write(self):
        # write out the new popolo data (tidied up a bit)
        out_json = json.dumps(self.popolo_data, sort_keys=True, indent=4 )
        out_json = re.sub(r'\s+\n', '\n', out_json)
        out_json += "\n"
        open( '../south-africa-popolo.json', 'w' ).write( out_json );


if __name__ == '__main__':
    ChangeApplier().run()
