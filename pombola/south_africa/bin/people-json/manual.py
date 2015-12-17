from utils import add_membership, idFactory, PROVINCES


def parse(data):
    for person in data['persons'].values():
        person['slug'] = person['name'].lower().replace(' ', '-')

    # There are three non-Assembly/NCOP people in the executive
    no_house = 0
    for p in data['persons'].values():
        if not [ y for y in p['memberships'] if 'house' in y['organization_id'] ]:
            no_house += 1
    assert no_house == 3

    na_manual = {
        'Cassel Charlie Mathale': { 'start_date': '2013-07-15' },
        'Wayne Maxim Thring': { 'start_date': '2013-06-21' },
        'Masenyani Richard Baloyi': { 'end_date': '2013-07-10' },
        'Letlapa Moroatshoge Mphahlele': { 'end_date': '2013-07-11', 'end_reason': 'Ceased to be a member under section 47(3)(c) of the Constitution (changed party)' },
        # 'Mpethi': { 'start_date': ? },
        'Ntopile Marcel Kganyago': { 'end_date': '2013-07-17', 'end_reason': 'Died' },
        'Nqabayomzi Lawrence Kwankwa': { 'start_date': '2013-08-06' },
        'Loretta Jacobus': { 'end_date': '2013-08-01' },
    }

    ncop_manual = {
        'Rory Dean MacPherson': { 'party': 'DA', 'end_date': '2009-05-29', 'province': 'KwaZulu-Natal' },
            'Robert Alfred Lees': { 'start_date': '2009-06-11' },
        'Sheery Su-Huei Cheng': { 'party': 'DA', 'end_date': '2010-09-30', 'province': 'Gauteng' },
            'Beverley Lynette Abrahams': { 'start_date': '2010-10-01' },
        'Timothy Duncan Harris': { 'party': 'DA', 'end_date': '2010-09-09', 'province': 'Western Cape' },
            'Theodorus Barnardus Beyleveldt': { 'party': 'DA', 'start_date': '2010-10-12', 'end_date': '2011-07-10', 'end_reason': 'Died', 'province': 'Western Cape' },
            'Denis Joseph': { 'start_date': '2011-10-20' },
        'Armiston Watson': { 'party': 'DA', 'end_date': '2011-11-07', 'province': 'Mpumalanga' },
            'Velly Makasana Manzini': { 'start_date': '2011-11-08' },
        'Tlhalefi Andries Mashamaite': { 'party': 'ANC', 'end_date': '2012-05-08', 'province': 'Limpopo' },
            'Thabo Lucas Makunyane': { 'start_date': '2012-05-22' },
        'Zukisa Cheryl Faku': { 'start_date': '2013-04-25' },
        'Mokoane Collen Maine': { 'end_date': '2013-08-01' }, # XXX
    }

    for person in data['persons'].values():
        name = person['name']
        mships = person['memberships']
        mship = [ x for x in mships if 'ncop' in x['organization_id'] and x['role'] == 'Delegate' ]
        if mship:
            # Present, and has NCOP membership entry. Set a start and possibly end date.
            mship = mship[0]
            assert 'start_date' not in mship
            n = ncop_manual.pop(name, {})
            mship['start_date'] = n.get('start_date', '2009-05-07')
            if 'end_date' in n and 'end_date' not in mship:
                mship['end_date'] = n['end_date']
        elif name in ncop_manual:
            # Present, but has no NCOP membership entry
            n = ncop_manual.pop(name)
            add_membership(person, { 'organization_id': 'org.mysociety.za/house/ncop',
                'label': 'Delegate for %s' % n['province'], 'role': 'Delegate',
                'area': { 'id': 'org.mysociety.za/mapit/code/p/' + PROVINCES[n['province']], 'name': n['province'] },
                'start_date': n.get('start_date', '2009-05-07'),
                'end_date': n['end_date'],
                'end_reason': n.get('end_reason', 'Resigned'),
            })
        mship = [ x for x in mships if 'house/na' in x['organization_id'] and x['role'] == 'Member' ]
        if mship:
            mship = mship[0]
            n = na_manual.pop(name, {})
            if 'start_date' not in mship:
                mship['start_date'] = n.pop('start_date', '2009-05-06')
            if n:
                assert 'end_date' not in mship
                mship['end_date'] = n['end_date']
                mship['end_reason'] = n.get('end_reason', 'Resigned')
        elif name in na_manual:
            raise Exception

    # The ones left have no person entry at all.
    for name, d in ncop_manual.items():
        id = idFactory.new('person')
        given_names, family_name = name.rsplit(None, 1)
        person = {
            'id': id,
            'name': name,
            'given_names': given_names,
            'family_name': family_name,
            'slug': name.lower().replace(' ', '-'),
        }
        add_membership(person, { 'organization_id': data['organizations'][d['party']]['id'] })
        add_membership(person, {
            'organization_id': 'org.mysociety.za/house/ncop',
            'label': 'Delegate for %s' % d['province'],
            'role': 'Delegate',
            'area': { 'id': 'org.mysociety.za/mapit/code/p/' + PROVINCES[d['province']], 'name': d['province'] },
            'start_date': d.get('start_date', '2009-05-07'),
            'end_date': d['end_date'],
            'end_reason': d.get('end_reason', 'Resigned'),
        })
        data['persons'][name] = person

    return data

