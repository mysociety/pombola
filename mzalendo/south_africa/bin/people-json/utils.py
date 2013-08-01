import os

data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data') + '/'

PROVINCES = {
    'Eastern Cape': 'EC',
    'Free State': 'FS',
    'Gauteng': 'GT',
    'KwaZulu-Natal': 'KZN',
    'Limpopo': 'LIM',
    'Mpumalanga': 'MP',
    'Northern Cape': 'NC',
    'North West': 'NW',
    'Western Cape': 'WC'
}

REASONS = {
    '2': 'Resigned',
    '3': 'Died',
    '4': 'Ceased to be a member under section 47(3)(c) of the Constitution (changed party)',
    '5': 'Elected President',
}

class IdFactory:
    counts = {}
    defaults = {}

    def max(self, typ, m):
        self.defaults[typ] = m

    def new(self, typ):
        default = self.defaults.get(typ, 0)
        self.counts[typ] = self.counts.setdefault(typ, default) + 1
        return 'org.mysociety.za/%s/%s' % (typ, self.counts[typ])

idFactory = IdFactory()

def add_membership(person, data):
    data.update(
        id = idFactory.new('membership'),
        person_id = person['id']
    )
    person.setdefault('memberships', []).append(data)
