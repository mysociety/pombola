import os, sys
import csv
import re

# Horrible boilerplate - there must be a better way :)
sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__) + '../../..'
    )
)


from pombola.core.models import Person, Organisation, OrganisationKind, PositionTitle, Position
from django.utils.text import slugify


reader = csv.DictReader( open(sys.argv[1], 'r') )

governmental = OrganisationKind.objects.get(slug='governmental')

for row in reader:
    if row['slug']:
        person = Person.objects.get(slug=row['slug'])
    else:
        # tidy up name and then loose search for it
        name = re.sub( r',\s*$', '', row['name'] )  # trailing comma
        name = re.sub( r'[A-Z]\.', '', name )       # drop initials
        name = re.sub( r'\s+', ' ', name )          # normalize whitespace
        name = name.strip()
        person = Person.objects.loose_match_name(name)

    if not person:
        print "Can't find person for '%s' (line %s)" % (row['name'], reader.line_num )
        continue

    # Find or create the committe
    committee_name = re.sub(r'[\s\-]+S\.O\..*$', '', row['committee'])

    committee, created = Organisation.objects.get_or_create(
        slug = slugify( committee_name ),
        defaults = dict(
            name = row['committee'],
            kind = governmental,
        ),
    )

    # Find the position title
    title = PositionTitle.objects.get(name=row['role'])

    # find or create the position
    position, created = Position.objects.get_or_create(
        person = person,
        organisation = committee,
        title = title,
        defaults = { 'category': 'political', },
    )

