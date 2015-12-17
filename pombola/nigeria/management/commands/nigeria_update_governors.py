import unicodecsv as csv

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import LabelCommand

from django.utils.text import slugify

from pombola.core.models import (
    Person, Organisation, Place, PositionTitle, Contact, ContactKind, ContentType
)

class Command(LabelCommand):

    help = 'Imports the Nigerian governor data from CSV.'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        # We'll need to reuse these a few times
        self.governor_position = PositionTitle.objects.get(slug='governor')
        self.member_position = PositionTitle.objects.get(slug='member')

        self.content_type_person = ContentType.objects.get_for_model(Person)

        self.contact_kind_website = ContactKind.objects.get(slug='website')
        self.contact_kind_email = ContactKind.objects.get(slug='email')
        self.contact_kind_phone = ContactKind.objects.get(slug='phone')
        self.contact_kind_fb = ContactKind.objects.get(slug='facebook')
        self.contact_kind_twitter = ContactKind.objects.get(slug='twitter')
        self.contact_kind_youtube = ContactKind.objects.get(slug='youtube')

    def save_contact_list(self, list, person, contact_kind):

        contacts = list.split(',')

        for contact in contacts:
            contact = contact.strip()

            # Contact might have a label, so try extract that
            label, _, contact = contact.rpartition(': ')

            # We might already have this, so get_or_create
            contact_object, created = Contact.objects.get_or_create(
                value = contact.strip(),
                object_id = person.id,
                content_type = self.content_type_person,
                kind = contact_kind,
            )

            if label:
                contact_object.note = label.strip()
                contact_object.save()

            if created:
                print 'Info: Created contact object ' + contact

    def handle_label(self, filename, **options):

        with open(filename) as f:

            # Use a DictReader so this is a bit more futureproof if the CSV changes.
            data = csv.DictReader(f)

            # Iterate over the remaining lines
            for person_csv in data:

                slug = slugify(person_csv['GOVERNOR'])

                # First, let's try get (or create) the person.
                person, created = Person.objects.get_or_create(slug=slug)

                if created:
                    print 'CREATED ' + slug
                else:
                    print 'Matched ' + slug

                # Update the name. Not needed for matches, but needed for new people.
                person.legal_name = person_csv['GOVERNOR']

                # Save changes made to the person
                person.save()

                # Get the state, essential to updating the governor position
                try:
                    state = Place.objects.get(
                        slug=slugify(person_csv['STATE']),
                        kind__slug = 'state',
                    )

                    # Get the person's governorship (or create it)
                    position_governor, created = person.position_set.get_or_create(
                        place=state,
                        title=self.governor_position,
                    )

                    # Update their governorship
                    if person_csv['TERM ENDS']:
                        position_governor.place = state
                        position_governor.title = self.governor_position
                        position_governor.category = 'Political'
                        position_governor.end_date = person_csv['TERM ENDS']
                    else:
                        print 'Info: Missing end of term!'

                    position_governor.save()

                    if created:
                        print 'Info: Created governorship position'

                except ObjectDoesNotExist:
                    print 'Unable to match state ' + person_csv['STATE']
                    exit(1)

                # Get the party, essential to updating the party position
                try:
                    party = Organisation.objects.get(
                        slug=slugify(person_csv['PARTY']),
                        kind__slug = 'party',
                    )

                    # Get the person's party membership (or create it)
                    position_party, created = person.position_set.get_or_create(
                        organisation=party,
                        title=self.member_position,
                    )

                    # Update their party membership
                    position_governor.organisation = party
                    position_governor.title = self.member_position
                    position_governor.category = 'Political'

                    position_party.save()

                    if created:
                        print 'Info: Created party position'

                except ObjectDoesNotExist:
                    print 'Unable to match party ' + person_csv['PARTY']
                    exit(1)

                for column, contact_kind in (
                    ('WEBSITE', self.contact_kind_website),
                    ('EMAIL', self.contact_kind_email),
                    ('NUMBERS', self.contact_kind_phone),
                    ('FACEBOOK', self.contact_kind_fb),
                    ('TWITTER', self.contact_kind_twitter),
                    ('YOUTUBE', self.contact_kind_youtube)
                ):
                    value = person_csv[column]
                    if value:
                        self.save_contact_list(value, person, contact_kind)

        print 'Done!'
