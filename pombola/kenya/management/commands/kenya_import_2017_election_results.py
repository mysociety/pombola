import csv
import os

from django.core.management.base import NoArgsCommand
from django.utils.text import slugify

from django.db.utils import IntegrityError

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from pombola.core.models import (
    AlternativePersonName, Organisation, Person, Place, PlaceKind, Position,
    PositionTitle, Identifier, ParliamentarySession)

from django.contrib.contenttypes.models import ContentType

from django_date_extensions.fields import ApproximateDate

from django.db.models import Q

results_directory = os.path.join(
    os.path.dirname(__file__), '..', '..', 'election_data_2017', 'results'
)

OLD_SESSION_END_DATE_STRING = '2017-07-16'  # When people packed up for the election
# Source: http://www.parliament.go.ke/the-national-assembly/house-business/legislative-calendar
NEW_SESSION_START_DATE_STRING = '2017-08-09'  # When the 2017 *sessions* should start
POSITIONS_INAUGURATION_DATE_STRING = '2017-08-31'  # When people actually took office

PARTY_MAP = {
    'party:33': 'kanu',
    'party:27': 'jubilee_party',
    'party:23': 'ford',
    'party:21': 'odm',
    'party:15': 'party-development-and-reform',
    'party:62': 'amani_national_congress',
    'party:12': 'wdm-k',
    'party:36': 'ccu',
    'party:48': 'economic-freedom-party',
    'party:67': 'maendeleo-chap-chap-party',
    'party:39': 'pdp',
    'party:9': 'knc',
    'party:54': 'chama-cha-mashinani',
    'party:31': 'kenya-patriots-party',
    'party:50': 'muungano-party',
    'party:40': 'nd',
    'party:46': 'frontier-alliance-party',
    'party:37': 'nap-k',  # 'napk' seems to be the same body, but less complete
    'party:13': 'democratic-party-kenya',
    'party:14': 'pnu',
}

YNR_ID_SCHEME_NAME = 'ynr-ke'

CONSTITUENCY_PARENT_OVERRIDES = {
    'suba-north-2013': 'homa-bay-county-2017',
    'suba-south-2013': 'homa-bay-county-2017'
}


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Command(NoArgsCommand):
    help = 'Import elected representatives from the 2017 election'

    def prepare_common_objects(self):

        parliament_house = Organisation.objects.get(slug='parliament')
        parliament_position_title = PositionTitle.objects.get(slug='member-national-assembly')
        self.parliamentary_session, _ = ParliamentarySession.objects.get_or_create(
            slug='na2017',
            defaults={
                'name': 'National Assembly 2017-',
                'start_date': NEW_SESSION_START_DATE_STRING,
                'end_date': '9999-12-31',
                'house': parliament_house,
                'position_title': parliament_position_title
            }
        )

        senate_house = Organisation.objects.get(slug='senate')
        senate_position_title = PositionTitle.objects.get(slug='senator')

        self.senate_session, _ = ParliamentarySession.objects.get_or_create(
            slug='s2017',
            defaults={
                'name': 'Senate 2017-',
                'start_date': NEW_SESSION_START_DATE_STRING,
                'end_date': '9999-12-31',
                'house': senate_house,
                'position_title': senate_position_title
            }
        )

        self.import_types = [
            {
                'file': 'senate.csv',
                'area_type': PlaceKind.objects.get(slug='county'),
                'area_term': self.senate_session,
                'area_suffix': '-county-2017',
                'position_org': senate_house,
                'position_title': senate_position_title
            },
            {
                'file': 'wo.csv',
                'area_type': PlaceKind.objects.get(slug='county'),
                'area_suffix': '-county',
                'position_org': parliament_house,
                'position_title': parliament_position_title,
                'position_subtitle': 'Women\'s representative'
            },
            {
                'file': 'na.csv',
                'area_type': PlaceKind.objects.get(slug='constituency'),
                'area_term': self.parliamentary_session,
                'area_suffix': '-2017',
                'position_org': parliament_house,
                'position_title': parliament_position_title
            }
        ]

        self.party_member_title = PositionTitle.objects.get(slug='member')

        self.person_content_type = ContentType.objects.get_for_model(Person)

    # This quickly sets the names and dates correctly for previous sessions
    def clean_previous_sessions(self):
        previous_parliamentary_session = ParliamentarySession.objects.get(
            slug='na2013'
        )
        previous_parliamentary_session.name = 'National Assembly 2013-2017'
        previous_parliamentary_session.end_date = OLD_SESSION_END_DATE_STRING
        previous_parliamentary_session.save()

        previous_senate_session = ParliamentarySession.objects.get(
            slug='s2013'
        )
        previous_senate_session.name = 'Senate 2013-2017'
        previous_senate_session.end_date = OLD_SESSION_END_DATE_STRING
        previous_senate_session.save()

    # This tidies up previous representatives
    def end_previous_memberships(self):

        for import_type in self.import_types:

            # For all of the positions of the right organisation, title and
            # category, which start *before* the inauguration date (which all
            # *new* positions have), set the end date correctly
            old_positions = Position.objects.filter(Q(
                organisation=import_type['position_org'],
                title=import_type['position_title'],
                category='political',
                start_date__lt=POSITIONS_INAUGURATION_DATE_STRING) & (
                    Q(end_date='future') |
                    Q(end_date='')
                )
            )

            for old_position in old_positions:
                old_position.end_date = OLD_SESSION_END_DATE_STRING
                old_position.save()

    def handle_noargs(self, **options):

        self.prepare_common_objects()

        self.clean_previous_sessions()

        self.end_previous_memberships()

        for import_type in self.import_types:

            csv_path = os.path.join(results_directory, import_type['file'])

            with open(csv_path) as csv_file:
                for row in csv.DictReader(csv_file):

                    print 'Importing {}'.format(row['name'])

                    # Let's sanity check some important things.

                    # Party?

                    if row['party_id'] != 'party:IND':

                        if row['party_id'] in PARTY_MAP:
                            party = Organisation.objects.get(slug=PARTY_MAP[row['party_id']])
                        else:
                            raise Exception('Party {} ({}) is not in map!'.format(row['party_name'], row['party_id']))

                    # Area?

                    print '\tTrying to find {} "{}"'.format(import_type['area_type'], row['post_label'])

                    area_slug = slugify(row['post_label']) + import_type['area_suffix']

                    try:
                        area = Place.objects.get(
                            slug=area_slug,
                            kind=import_type['area_type']
                        )

                    except ObjectDoesNotExist:
                        print '\tArea not found, creating!'

                        # New areas need a parent area, which we can get from
                        # the old area... if it's a constituency
                        if import_type['area_type'] == PlaceKind.objects.get(slug='constituency'):

                            old_area_slug = slugify(row['post_label']) + '-2013'

                            if old_area_slug in CONSTITUENCY_PARENT_OVERRIDES:

                                new_parent_area_slug = CONSTITUENCY_PARENT_OVERRIDES[old_area_slug]

                                print '\tParent area overriden to {}'.format(new_parent_area_slug)

                            else:

                                # So, find the old area based on the slug

                                print '\tAttempting to find old area {}'.format(old_area_slug)
                                old_area = Place.objects.get(slug=old_area_slug)

                                # Turn that old area's parent *name* into a new slug
                                new_parent_area_slug = slugify(old_area.parent_place.name) + '-county-2017'

                            print '\tAttempting to find new parent {}'.format(new_parent_area_slug)

                            # And turn that into the new parent area
                            new_parent_area = Place.objects.get(slug=new_parent_area_slug)

                            area = Place(
                                slug=area_slug,
                                name=row['post_label'],
                                kind=import_type['area_type'],
                                parent_place=new_parent_area
                            )

                        else:

                            area = Place(
                                slug=area_slug,
                                name=row['post_label'],
                                kind=import_type['area_type']
                            )

                    # If the area has a term, set that
                    if 'area_term' in import_type:
                        area.parliamentary_session = import_type['area_term']

                    area.save()

                    # Can we find the person from their YNR ID?

                    try:
                        identifier = Identifier.objects.get(
                            scheme=YNR_ID_SCHEME_NAME,
                            identifier=row['id'],
                            content_type=self.person_content_type
                        )

                        person = Person.objects.get(
                            id=identifier.object_id)

                        print bcolors.OKGREEN + '\tMatched on YNR ID' + bcolors.ENDC

                    except:

                        if row['mz_id']:
                            print '\tHas Mzalendo ID: {}'.format(row['mz_id'])

                            # Let's try get this person!

                            person = Person.objects.get(id=int(row['mz_id']))

                            print '\tMatched with {} by Mzalendo ID'.format(person.name)

                        # No Mzalendo ID? New person time!

                        else:

                            print '\tNo match, creating a new person!'

                            # Name is the only thing which doesn't get checked by a later update, so set here
                            person = Person(
                                legal_name=row['name'],
                                slug=slugify(row['name']),
                                title=row['honorific_prefix'],
                                gender=row['gender'].lower()
                            )

                            try:
                                person.save()
                            except IntegrityError:
                                # This will probably be a slug error.
                                person.slug = person.slug + '-2'
                                person.save()

                        identifier = Identifier(
                            identifier=row['id'],
                            scheme=YNR_ID_SCHEME_NAME,
                            content_type=self.person_content_type,
                            object_id=person.id
                        )
                        identifier.save()

                        print '\tAdded YNR ID to Mzalendo'

                    # At this point we have a person! Let's go!

                    # Assume YNR email addresses have all been checked off pretty recently
                    if row['email']:
                        if person.email != row['email']:
                            person.email = row['email']
                            print bcolors.OKBLUE + '\tUpdated email address: {}'.format(row['email']) + bcolors.ENDC
                        else:
                            print '\tEmail addresses match, not changing.'
                    else:
                        print '\tNo email address in YNR, not attempting update.'

                    # Assume YNR genders have all been checked off pretty recently
                    if row['gender']:
                        if person.gender != row['gender'].lower():
                            person.gender = row['gender'].lower()
                            print bcolors.OKBLUE + '\tUpdated gender: {}'.format(row['gender'].lower()) + bcolors.ENDC
                        else:
                            print '\tGender match, not changing.'

                    # Birthday

                    if row['birth_date']:
                        if person.date_of_birth != row['birth_date']:

                            if '/' in row['birth_date']:
                                # This is a date in DD/MM/YYYY (from YNR). Fix.
                                dob_parts = row['birth_date'].split('/')
                                dob = ApproximateDate(int(dob_parts[2]), int(dob_parts[1]), int(dob_parts[0]))
                            else:
                                # This is a year!
                                dob = ApproximateDate(int(row['birth_date']))

                            person.date_of_birth = dob
                            print bcolors.OKBLUE + '\tUpdated DOB: {}'.format(row['birth_date']) + bcolors.ENDC
                        else:
                            print '\tDOB match, not changing.'

                    # Save any of those changes
                    person.save()

                    # Positions time! First, their party membership.
                    # We have *no knowledge* of relevant start or end dates,
                    # so just make sure they exist as a member, and touch
                    # nothing else.

                    try:
                        _, created_party_position = Position.objects.get_or_create(
                            person=person,
                            organisation=party,
                            title=self.party_member_title,
                            category='political'
                        )

                        if created_party_position:
                            print '\tAdded new party position.'
                        else:
                            print '\tAlready has party position.'
                    except MultipleObjectsReturned:
                        print '\tMultiple party positions exist, leaving alone.'

                    # Finally, the all important elected role!

                    post_position, created_post_position = Position.objects.get_or_create(
                        person=person,
                        organisation=import_type['position_org'],
                        title=import_type['position_title'],
                        place=area,
                        category='political',
                        start_date=POSITIONS_INAUGURATION_DATE_STRING,
                        end_date='future'
                    )

                    if 'position_subtitle' in import_type:
                        post_position.subtitle = import_type['position_subtitle']
                        post_position.save()

                    if created_post_position:
                        print '\tAdded new post position.'
                    else:
                        print '\tAlready has post position.'
