def fix_province_name(province_name):
    if province_name == 'Kwa-Zulu Natal':
        return 'KwaZulu-Natal'
    else:
        return province_name

def fix_municipality_name(municipality_name):
    if municipality_name == 'Merafong':
        return 'Merafong City'
    else:
        return municipality_name

def all_initial_forms(name, squash_initials=False):
    '''Generate all initialized variants of first names

    >>> for name in all_initial_forms('foo Bar baz quux', squash_initials=True):
    ...     print name
    foo Bar baz quux
    f Bar baz quux
    fB baz quux
    fBb quux

    >>> for name in all_initial_forms('foo Bar baz quux'):
    ...     print name
    foo Bar baz quux
    f Bar baz quux
    f B baz quux
    f B b quux
    '''
    names = name.split(' ')
    n = len(names)
    if n == 0:
        yield name
    for i in range(0, n):
        if i == 0:
            yield ' '.join(names)
            continue
        initials = [name[0] for name in names[:i]]
        if squash_initials:
            result = [''.join(initials)]
        else:
            result = initials
        yield ' '.join(result + names[i:])

class LocationNotFound(Exception):
    pass
